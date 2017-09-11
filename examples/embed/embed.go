package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/davidbyttow/govips"
)

func run(inputFile, outputFile string) error {
	in, err := vips.NewImageFromFile(inputFile,
		vips.IntInput("access", int(vips.AccessSequentialUnbuffered)))
	if err != nil {
		return err
	}

	out := in.Embed(10, 10, 1000, 1000,
		vips.IntInput("extend", int(vips.ExtendCopy)))

	out.WriteToFile(outputFile)
	return nil
}

var (
	flagIn  = flag.String("in", "", "file to load")
	flagOut = flag.String("out", "", "file to write out")
)

func main() {
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "embed -in input_file -out output_file")
	}
	flag.Parse()

	vips.Startup(nil)
	defer vips.Shutdown()

	err := run(*flagIn, *flagOut)
	if err != nil {
		os.Exit(1)
	}
}
