"""Use a temporary dbt instance to generate dependency docs
"""
import os, sys
import argparse
import logging
from pathlib import Path
import subprocess

HERE = Path(__file__)
print(HERE)

logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

log_file_path = "dump_snowflake_databases.log"
log_format = "%(name)s - %(asctime)s - %(levelname)s - %(message)s"
file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(log_format))
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

error_file_path = "dump_snowflake_databases.errors.log"
error_handler = logging.FileHandler(error_file_path)
error_handler.setFormatter(logging.Formatter(log_format))
error_handler.setLevel(logging.WARN)
logger.addHandler(error_handler)

def run(args):
    print(args.filepath)

def command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath", help="A spreadsheet containing the dependencies")
    args = parser.parse_args()
    run(args)

if __name__ == '__main__':
    command_line()

"""
--project-dir
--profiles-dir
"""
