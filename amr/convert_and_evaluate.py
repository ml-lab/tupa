#!/usr/bin/env python3

import argparse
import glob
import sys

import convert
from amrutil import evaluate, Scores
from ucca.ioutil import passage2file

desc = """Parses files in AMR format, converts to UCCA standard format,
converts back to the original format and evaluates using smatch.
"""


def main():
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument("filenames", nargs="+",
                           help="file names to convert and evaluate")
    argparser.add_argument("-v", "--verbose", action="store_true",
                           help="print evaluation results for each file separately")
    argparser.add_argument("-o", "--outdir",
                           help="output directory (if unspecified, files are not written)")
    args = argparser.parse_args()

    scores = []
    for pattern in args.filenames:
        filenames = glob.glob(pattern)
        if not filenames:
            raise IOError("Not found: " + pattern)
        for filename in filenames:
            sys.stdout.write("\rConverting '%s'" % filename)
            sys.stdout.flush()
            with open(filename, encoding="utf-8") as f:
                for passage, (ref, amr_id) in zip(convert.from_amr(f), convert.from_amr(f, return_amr=True)):
                    if args.outdir:
                        outfile = "%s/%s.xml" % (args.outdir, passage.ID)
                        sys.stderr.write("Writing '%s'...\n" % outfile)
                        passage2file(passage, outfile)
                    try:
                        guessed = convert.to_amr(passage, amr_id)
                    except Exception as e:
                        raise ValueError("Error converting %s back from AMR" % filename) from e
                    if args.outdir:
                        outfile = "%s/%s.txt" % (args.outdir, passage.ID)
                        sys.stderr.write("Writing '%s'...\n" % outfile)
                        with open(outfile, "w", encoding="utf-8") as f_out:
                            print(str(guessed), file=f_out)
                    try:
                        scores.append(evaluate(guessed, ref, verbose=args.verbose))
                    except Exception as e:
                        raise ValueError("Error evaluating conversion of %s" % filename) from e
    print()
    if args.verbose and len(scores) > 1:
        print("Aggregated scores:")
    Scores.aggregate(scores).print()

    sys.exit(0)


if __name__ == '__main__':
    main()