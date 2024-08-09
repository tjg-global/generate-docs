# generate-docs

Use the DBT object hierarchy viewer to view arbitrary object dependency models

## Background

The dbt object viewer is an easy way to view an object hierarchy, especially
when coupled with its tags and model-selection capabilities. We'd previously
wondered whether the JS functionality could be decoupled from the DBT codebase
and be reused. But then someone had the bright idea that we could simply generate
a dbt project with the models & dependencies we needed and use dbt's own processes
to generate and display the data lineage.

## Installation

Use pip to install the package, eg: `pip install git+https://github.com/tjg-global/generate-docs.git`
(or clone and use `pip install -e ...`). This will create a command-line entrypoint
`generate_docs.exe` in your venv or user scripts area -- depending on the context
into which you pip-installed.

## Data Spreadsheet

Prepare a spreadsheet with at least one sheet named `Dependencies` and, optionally,
a sheet named `Objects`.

The `Dependencies` sheet will have two columns, the first called `Object` and
the second `Depends On`, eg:

| Object     | Depends On       |
|------------|------------------|
| Object A   | Object B         |
| Object B   |                  |

The optional `Objects` sheet will have four columns: Object, Group, Tags, Description
While the columns should always be there, their contents are optional except for `Object`
which must be there for the data to make sense.

* The `Object` data should correspond to an object or dependency in the `Dependencies` data
above.

* The `Group` data is, optionally, a way of grouping objects together as, eg,
Bronze / Silver / Gold or Staging / Presentation. If it's not present, the object
will fall into a default group.

* The `Tags` data is, optionally, a comma-separated list of tags which can be anything
at all, including spaces etc.

* The `Description` is an arbitrary text field [currently unused] which could be used,
eg to populate the model description in the dbt project metadata

| Object     | Group            | Tags                 | Description          |
|------------|------------------|----------------------|----------------------|
| Object A   | SomeGroup        | Tag X, Tag Y         |                      |
| Object B   | OtherGroup       | Tag Z, Tag Y         | An Object which is B |

*NB only the `Dependencies` sheet is needed: the `Objects` sheet is only
presenting useful additional metadata to enhance the view*

## Usage

With a spreadsheet as above called, eg `Database.xlsx`:

`generate_docs /path/to/database.xlsx`

This will generate a temporary dbt project, populate its models using the data
from the spreadsheet, and then generate and launch the docs in a browser using
standard dbt functionality.

## Options

At present the only additional command-line option is `--target-dirpath` which will
override the use of the temporary directory area when generating the dbt project.
This might be useful if you wanted, eg, to use the tool to do the spadework to
generate the project and then to enhance it and maintain it by hand.

## Future Enhancements?

- As it stands, this approach works quite well with, eg, the fairly large ~1,000
models in the OOH DW. However, it might be interesting to partition those models
into their dbt equivalents: seeds, sources, models, externals etc.

- To keep the dbt model space smaller even before filtering, it might be useful to
offer an option to generate only those models which, eg depended on a particular
object or matched some tags.

- Given a Snowflake database, you can use the `account_usage.object_dependencies` view
to determine dependencies, including for stages, tasks etc. It might be interesting
to point the tool at a Snowflake database and let it pull the data out directly.

