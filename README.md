# LostTime
Orienteering utilities on the web. Visit <http://LostTimeOrienteering.com> to simplify your workflow and recover some lost time.

The current goal of LostTime is not to replace event management software, but to make tasks before and after an event easier. Customization on a per-club basis is expected.

# Usage

## Entries
**Input**: any number of .csv files representing entries  
**Output**: single .csv file ready for import into SportSoftware  
For the input .csv files, if the header line contains any of the following strings, its data will be included in the output: `bib`, `first`, `last`, `club` or `school`, `class`, `sex` or `gen`, `punch` or `card`, `rent`, and `nc`. Checking is loose: a column titled `First Name` will match `first`. *(Special case, the word `emergency` does not match `gen` or `nc`.)*

## Event Results
**Input**: single IOF v3 .xml `<ResultList>` file  
**Output**: single .html page, results by class, sorted, and scored  
Scoring methods include: Time (no score), Ratio to winner (1000pts), World Cup (100, 95, 92, 90, ...), or Alphabetical sorting (no placement).

# Backlog
## Entries
- make the default output an IOF xml `<EntryList>` file, for greater inter-operability

## Event Results
- Calculate and output an additional html page with team results, starting with COC WIOL scoring algorithm.

## Series Results
- Allow multiple events to be combined into a series for scoring purposes
- Configure different series scoring parameters
- Calculate and output html page of series results


# Technical Notes
## Architecture
This is a Flask application with a SQLite backend. There is currently no front-end framework; data is passed to the Jinja2 template engine that comes bundled with Flask.
## Development and Testing

## Database Management

## Deployment

 
