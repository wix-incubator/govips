package gimage

// #cgo pkg-config: vips
// #include "bridge.h"
import "C"

func vipsForeignFindLoad(filename string) (string, error) {
	c_filename := C.CString(filename)
	defer freeCString(c_filename)

	c_operationName := C.vips_foreign_find_load(c_filename)
	if c_operationName == nil {
		return "", ErrUnsupportedImageFormat
	}
	return C.GoString(c_operationName), nil
}

func vipsForeignFindLoadBuffer(bytes []byte) (string, error) {
	c_operationName := C.vips_foreign_find_load_buffer(
		byteArrayPointer(bytes),
		C.size_t(len(bytes)))
	if c_operationName == nil {
		return "", ErrUnsupportedImageFormat
	}
	return C.GoString(c_operationName), nil
}

func vipsForeignFindSave(filename string) (string, error) {
	c_filename := C.CString(filename)
	defer freeCString(c_filename)

	c_operationName := C.vips_foreign_find_save(c_filename)
	if c_operationName == nil {
		return "", ErrUnsupportedImageFormat
	}
	return C.GoString(c_operationName), nil
}

func vipsForeignFindSaveBuffer(filename string) (string, error) {
	c_filename := C.CString(filename)
	defer freeCString(c_filename)

	c_operationName := C.vips_foreign_find_save_buffer(c_filename)
	if c_operationName == nil {
		return "", ErrUnsupportedImageFormat
	}
	return C.GoString(c_operationName), nil
}

func vipsInterpolateNew(name string) (*C.VipsInterpolate, error) {
	c_name := C.CString(name)
	defer freeCString(c_name)

	interp := C.vips_interpolate_new(c_name)
	if interp == nil {
		return nil, ErrInvalidInterpolator
	}
	return interp, nil
}

func vipsOperationNew(name string) *C.VipsOperation {
	c_name := C.CString(name)
	defer freeCString(c_name)
	return C.vips_operation_new(c_name)
}

func vipsFilenameSplit8(file string) (string, string) {
	c_file := C.CString(file)
	defer freeCString(c_file)

	c_filename := C.CString(STRING_BUFFER)
	defer freeCString(c_filename)

	c_optionString := C.CString(STRING_BUFFER)
	defer freeCString(c_optionString)

	C.vips__filename_split8(c_file, c_filename, c_optionString)

	fileName := C.GoString(c_filename)
	optionString := C.GoString(c_optionString)
	return fileName, optionString
}
