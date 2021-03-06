#!/usr/bin/python3

import argparse
import http.client
import os
import csv
import json
import dateutil.parser


def main(file_path, delimiter, max_rows, elastic_index, json_struct, datetime_field, elastic_type, elastic_address, id_column):
    endpoint = '/_bulk'
    if max_rows is None:
      max_rows_disp = "all"
    else:
      max_rows_disp = max_rows

    print("")
    print(" ----- CSV to ElasticSearch ----- ")
    print("Importing %s rows into `%s` from '%s'" % (max_rows_disp, elastic_index, file_path))
    print("")

    count = 0
    headers = []
    headers_position = {}
    to_elastic_string = ""
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter, quotechar='"')
        for row in reader:
            if count == 0:
                for iterator, col in enumerate(row):
                    headers.append(col)
                    headers_position[col] = iterator
            elif max_rows is not None and count >= max_rows:
                print('Max rows imported - exit')
                break
            elif len(row[0]) == 0:    # Empty rows on the end of document
                print("Found empty rows at the end of document")
                break
            else:
                pos = 0
                if os.name == 'nt':
                    _data = json_struct.replace("^", '"')
                else:
                    _data = json_struct.replace("'", '"')
                _data = _data.replace('\n','').replace('\r','')
                for header in headers:
                    if header == datetime_field:
                        datetime_type = dateutil.parser.parse(row[pos])
                        _data = _data.replace('"%' + header + '%"', '"{:%Y-%m-%dT%H:%M}"'.format(datetime_type))
                    else:
                        try:
                            int(row[pos])
                            _data = _data.replace('"%' + header + '%"', row[pos])
                        except ValueError:
                            _data = _data.replace('%' + header + '%', row[pos])
                    pos += 1
                # Send the request
                if id_column is not None:
                    index_row = {"index": {"_index": elastic_index,
                                           "_type": elastic_type,
                                           '_id': row[headers_position[id_column]]}}
                else:
                    index_row = {"index": {"_index": elastic_index, "_type": elastic_type}}
                json_string = json.dumps(index_row) + "\n" + _data + "\n"
                to_elastic_string += json_string
            count += 1

    print('Reached end of CSV - creating file...')

    file = open("body.json","w")  
    file.write(to_elastic_string)
    file.close()
    
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CSV to ElasticSearch.')

    parser.add_argument('--elastic-address',
                        required=False,
                        type=str,
                        default='localhost:9200',
                        help='Your elasticsearch endpoint address')
    parser.add_argument('--csv-file',
                        required=True,
                        type=str,
                        help='path to csv to import')
    parser.add_argument('--json-struct',
                        required=True,
                        type=str,
                        help='json to be inserted')
    parser.add_argument('--elastic-index',
                        required=True,
                        type=str,
                        help='elastic index you want to put data in')
    parser.add_argument('--elastic-type',
                        required=False,
                        type=str,
                        default='stop',
                        help='Your entry type for elastic')
    parser.add_argument('--max-rows',
                        type=int,
                        default=None,
                        help='max rows to import')
    parser.add_argument('--datetime-field',
                        type=str,
                        help='datetime field for elastic')
    parser.add_argument('--id-column',
                        type=str,
                        default=None,
                        help='If you want to have index and you have it in csv, this the argument to point to it')
    parser.add_argument('--delimiter',
                        type=str,
                        default=",",
                        help='If you want to have a different delimiter than ;')

    parsed_args = parser.parse_args()

    main(file_path=parsed_args.csv_file, delimiter = parsed_args.delimiter, json_struct=parsed_args.json_struct,
         elastic_index=parsed_args.elastic_index, elastic_type=parsed_args.elastic_type,
         datetime_field=parsed_args.datetime_field, max_rows=parsed_args.max_rows,
         elastic_address=parsed_args.elastic_address, id_column=parsed_args.id_column)
