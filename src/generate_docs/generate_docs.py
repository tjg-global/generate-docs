"""Use a temporary dbt instance to generate dependency docs
"""
import os, sys
import argparse
from collections import namedtuple, defaultdict
import logging
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import openpyxl

HERE = Path(__file__).parent
NAME = HERE.stem
DBT_LAYOUT = HERE / ".." / "dbt-template"

logger = logging.getLogger(NAME)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.DEBUG)
logger.addHandler(stdout_handler)

log_file_path = f"{NAME}.log"
log_format = "%(name)s - %(asctime)s - %(levelname)s - %(message)s"
file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(log_format))
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

error_file_path = f"{NAME}.errors.log"
error_handler = logging.FileHandler(error_file_path)
error_handler.setFormatter(logging.Formatter(log_format))
error_handler.setLevel(logging.WARN)
logger.addHandler(error_handler)

def to_identifier(s):
    """Turn a string into a valid identifier

    Remove non-alphanumerics and join back with underscores
    """
    return "_".join(i for i in re.findall(r"[a-zA-z0-9._]*", s) if i)

def data_from_spreadsheet(xlsx_filepath, sheet_name):
    """Generate a namedtuple for each row of data

    The tuple field names are taken from the first row (adapted if needed
    to be valid identifier names). The tuple values are taken from the remaining
    non-empty rows of the sheet.
    """
    xlsx_filepath = Path(xlsx_filepath)
    wb = openpyxl.load_workbook(
        xlsx_filepath,
        data_only=True, read_only=True
    )
    if sheet_name not in wb:
        logger.warn("Sheet %s not found in %s", sheet_name, xlsx_filepath)
        return
    ws = wb[sheet_name]
    irows = ws.iter_rows()

    #
    # Create a namedtuple from the header rows
    #
    headers = [to_identifier(c.value) for c in next(irows)]
    tuple_name = to_identifier(xlsx_filepath.stem + " " + sheet_name)
    DataTuple = namedtuple(tuple_name, headers)

    #
    # Yield each data row as an instance of the namedtuple
    #
    for row in irows:
        if any(c.value for c in row): # Skip entirely blank rows
            yield DataTuple._make(c.value for c in row)

def copy_dbt_layout(target_dirpath, dirname):
    """Copy an empty dbt project into a temporary area
    """
    target_dirpath = Path(target_dirpath or tempfile.mkdtemp())
    dbt_dirpath = target_dirpath / dirname
    logger.debug("Copying dbt layout to %s", dbt_dirpath)
    shutil.copytree(DBT_LAYOUT, dbt_dirpath, dirs_exist_ok=True)
    return dbt_dirpath

def get_objects_from_xlsx(xlsx_filepath):
    """Read dependencies and (optionall) objects from an Excel workbook
    """
    #
    # Read dependencies first because they're needed
    # when building the objects
    #
    dependencies = {}
    objects = {}
    for dep in data_from_spreadsheet(xlsx_filepath, "Dependencies"):
        object_name = to_identifier(dep.Object.strip())
        if not dep.Depends_On:
            continue
        dep_name = to_identifier(dep.Depends_On.strip())
        dependencies.setdefault(object_name, set()).add(dep_name)
        #
        # Create an object entry for anything which is listed as an
        # object or as a dependency. (This is last is because might
        # have deactivated objects which are still listed as deps)
        #
        objects[object_name] = {}
        objects[dep_name] = {}

    #
    # Update object metadata from an Objects sheet if it exists
    #
    for object in data_from_spreadsheet(xlsx_filepath, "Objects"):
        object_name = to_identifier(object.Object.strip())
        tags = set(t.strip() for t in (object.Tags or "").split(",") if t.strip())
        if object.Group:
            tags.add(object.Group)
        objects.setdefault(object_name, {}).update(dict(
            group=object.Group,
            description=object.Description,
            tags=tags
        ))

    #
    # Add dependencies
    #
    for object_name, depends_on in dependencies.items():
        print("%s depends on %s" % (object_name, depends_on))
        if depends_on:
            for dep in depends_on:
                objects.setdefault(object_name, {}).setdefault('depends_on', set()).add(dep)

    return objects

def model_contents(object):
    """Generate the contents of a fake model for this object

    To have useful docs generated, we need dependencies and tags
    """
    for dep in object.get('depends_on', []):
        yield "-- depends on {{ref('%s')}}" % dep

    tags = object.get("tags", []) or []
    if tags:
        yield "{{config(tags=[%s])}}" % ",".join("'%s'" % t for t in tags)

def write_one_model(model_filepath, object):
    """Write the contents of the fake model to the appropriate file
    """
    with model_filepath.open("w") as f:
        for content in model_contents(object):
            f.write(content + "\n")

def write_models(dbt_dirpath, objects):
    """Write each object as a model with the correct dependencies
    """
    models_dirpath = dbt_dirpath / "models"
    for object_name, object in objects.items():
        logger.info("Writing model for %s", object_name)
        group = (object.get('group') or "").strip() or "database"
        model_dirpath = models_dirpath / group
        model_dirpath.mkdir(exist_ok=True)
        model_filepath = model_dirpath / (object_name + ".sql")
        write_one_model(model_filepath, object)

def dbt_run(dbt_root, *commands):
    """Run a dbt command with standard parameters
    """
    dbt_command = ["dbt"] + list(commands) + ["--project-dir", dbt_root, "--profiles-dir", dbt_root]
    subprocess.run(dbt_command, check=True)

def dbt_generate_docs(dbt_dirpath):
    """Run the standard dbt docs commands against our generated directory
    """
    dbt_root = str(dbt_dirpath)
    dbt_run(dbt_root, "docs", "generate")
    dbt_run(dbt_root, "docs", "serve")

def run(args):
    """Merge command-line args with defaults and run core functions
    """
    xlsx_filepath = Path(args.xlsx_filepath)
    #
    # Extract the objects and their dependencies from the specified spreadsheet
    # Copy the template DBT project to a temp or other directory
    # Write the models corresponding to the objects into the dbt project
    #
    objects = get_objects_from_xlsx(xlsx_filepath)
    dbt_dirpath = copy_dbt_layout(args.target_dirpath, xlsx_filepath.stem)
    write_models(dbt_dirpath, objects)
    dbt_generate_docs(dbt_dirpath)

def command_line():
    """Do basic command-line arg parsing and hand off to `run`
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx_filepath", help="A spreadsheet containing the dependencies")
    parser.add_argument("--target-dirpath", help="Directory to build docs in (defaults to a random temp directory)")
    args = parser.parse_args()
    run(args)

if __name__ == '__main__':
    command_line()

"""
--project-dir
--profiles-dir
"""
