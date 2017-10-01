package vips_test

import (
	"testing"

	"github.com/davidbyttow/govips"
)

func TestOptionPrimitives(t *testing.T) {
	var b bool
	var i int
	var d float64
	var s string
	options := []vips.VipsOption{
		vips.InputBool("b", true),
		vips.InputInt("i", 42),
		vips.InputDouble("d", 42.2),
		vips.InputString("s", "hi"),
		vips.OutputBool("b", &b),
		vips.OutputInt("i", &i),
		vips.OutputDouble("d", &d),
		vips.OutputString("s", &s),
	}

	for i := 0; i < 8; i++ {
		opt := options[i]
		switch opt.(type) {
		case vips.VipsInput:
			i := opt.(vips.VipsInput)
			i.Serialize()
		case vips.VipsOutput:
			o := opt.(vips.VipsOutput)
			o.Deserialize()
		}
	}
}
