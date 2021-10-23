#!/usr/bin/env python3

###########################################################################################################
# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause
###########################################################################################################

import csv
import os
import sys
import xlrd


def invalid_filename(filename):
    if not filename.endswith(".csv"):
        raise SystemError(f"{filename} isn't a csv format!")


def excel2json(filename, sheet="system view"):
    data = {}
    try:
        if os.access(filename, os.R_OK):
            wb = xlrd.open_workbook(filename)
            sh = wb.sheet_by_name(sheet)
            for rownum in range(1, sh.nrows):
                row_values = sh.row_values(rownum)
                metric = row_values[0]
                val = row_values[1]
                data[metric] = val
        else:
            raise SystemExit(f"{filename} not accessible")
    except xlrd.XLRDError as e:
        print(e)
        sys.exit(1)
    return data


def csv2json(filename):
    data = {}
    try:
        if os.access(filename, os.R_OK):
            with open(filename, encoding="utf-8") as csvf:
                csvReader = csv.DictReader(csvf)
                for rows in csvReader:
                    key = rows["metrics"]
                    data[key] = float(rows["avg"])
        else:
            raise SystemExit(f"{filename} not accessible")
    except KeyError as invalid_csv_key:
        raise SystemExit() from invalid_csv_key
    return data


def compare_metrics(metriclist, datalist, fields, out):
    if not metriclist:
        metriclist = [
            m
            for m in datalist[0].keys()
            if m.startswith("metric_TMA")
            or m
            in [
                "metric_CPU operating frequency (in GHz)",
                "metric_CPU utilization %",
                "metric_CPU utilization% in kernel mode",
                "metric_CPI",
            ]
        ]
    print("comparing predefined metrics only")
    if not invalid_filename(out):
        with open(out, "w") as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            csvwriter.writerow(fields)
            for metric in metriclist:
                rowlines = []
                rowlines.append(metric)
                for data in datalist:
                    if metric in data:
                        rowlines.append(data[metric])
                    else:
                        rowlines.append("NA")
                csvwriter.writerow(rowlines)


def compare_metrics_all(datalist, fields, out):
    print("comparing all metrics in the summary sheet")
    if not invalid_filename(out):
        with open(out, "w") as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(
                csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
            )
            csvwriter.writerow(fields)
            allkeys = []
            for data in datalist:
                for k in data:
                    allkeys.append(k)
            uniquekeys = list(set(allkeys))
            for metric in uniquekeys:
                rowlines = []
                rowlines.append(metric)
                for data in datalist:
                    if metric in data:
                        rowlines.append(data[metric])
                    else:
                        rowlines.append("NA")
                csvwriter.writerow(rowlines)


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Data Formatter")
    parser.add_argument(
        "-f",
        "--files",
        type=str,
        default=None,
        help='two or more excel/csv files delimited by "," and to be converted to json',
    )
    parser.add_argument(
        "-m",
        "--metriclist",
        nargs="*",
        type=str,
        default=[],
        help='metric list to be compared (use "-m d" for default metric list)',
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="compareFile.csv",
        help="output file to be used",
    )
    parser.add_argument(
        "-p",
        "--perfspect",
        dest="perfspect",
        default=False,
        action="store_true",
        help="metric.average.csv files generated by PerfSpect",
    )

    args = parser.parse_args()
    if args.files:
        filenames = args.files.split(",")
    else:
        raise SystemError("-f or --files is a required flag")

    print("comparing Files: ", filenames)
    jsondata = []
    fields = ["Metric"]
    for filename in filenames:
        if args.perfspect:
            jsondata.append(csv2json(filename))
        else:
            jsondata.append(excel2json(filename))
        fields.append(filename)

    if args.metriclist:
        # use "-m d" for predefined metriclist (all TMA and basic metrics)
        metriclist = args.metriclist
        if args.metriclist == ["d"]:
            metriclist = []
        compare_metrics(metriclist, jsondata, fields, args.output)
    else:
        compare_metrics_all(jsondata, fields, args.output)
    print("\nData compared and stored at", args.output)


main()