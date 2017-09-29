#!/usr/bin/python

# Walk vips and generate member definitions for all operators
# based on libvips/gen-operators.py

import datetime
import logging
import re
import sys

import gi
gi.require_version('Vips', '8.0')
from gi.repository import Vips, GObject

vips_type_image = GObject.GType.from_name("VipsImage")
vips_type_operation = GObject.GType.from_name("VipsOperation")
param_enum = GObject.GType.from_name("GParamEnum")

today = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

preamble ='''\
package vips

//golint:ignore

/***
 * NOTE: This file is autogenerated so you shouldn't modify it.
 * See scripts/gen-operators.py
 *
 * Generated at %s
 */

// #cgo pkg-config: vips
// #include "vips/vips.h"
import "C"\
''' % today

go_types = {
  "gboolean" : "bool",
  "gchararray" : "string",
  "gdouble" : "float64",
  "gint" : "int",
  "VipsBlob" : "*Blob",
  "VipsImage" : "*Image",
  "VipsInterpolate": "*Interpolator",
  "VipsOperationMath" : "OperationMath",
  "VipsOperationMath2" : "OperationMath2",
  "VipsOperationRound" : "OperationRound",
  "VipsOperationRelational" : "OperationRelational",
  "VipsOperationBoolean" : "OperationBoolean",
  "VipsOperationComplex" : "OperationComplex",
  "VipsOperationComplex2" : "OperationComplex2",
  "VipsOperationComplexget" : "OperationComplexGet",
  "VipsDirection" : "Direction",
  "VipsAngle" : "Angle",
  "VipsAngle45" : "Angle45",
  "VipsCoding": "Coding",
  "VipsInterpretation": "Interpretation",
  "VipsBandFormat": "BandFormat",
  "VipsOperationMorphology": "OperationMorphology",
}

options_method_names = {
  "gboolean" : "Bool",
  "gchararray" : "String",
  "gdouble" : "Double",
  "gint" : "Int",
  "VipsArrayDouble" : "DoubleArray",
  "VipsArrayImage" : "ImageArray",
  "VipsBlob" : "Blob",
  "VipsImage" : "Image",
  "VipsInterpolate" : "Interpolator",
}

def get_type(prop):
  return go_types[prop.value_type.name]


def get_options_method_name(prop):
  # Enums use their values
  if GObject.type_is_a(param_enum, prop):
    return "Int"
  return options_method_names[prop.value_type.name]


def find_required(op):
  required = []
  for prop in op.props:
    flags = op.get_argument_flags(prop.name)
    if not flags & Vips.ArgumentFlags.REQUIRED:
      continue
    if flags & Vips.ArgumentFlags.DEPRECATED:
      continue

    required.append(prop)

  def priority_sort(a, b):
    pa = op.get_argument_priority(a.name)
    pb = op.get_argument_priority(b.name)

    return pa - pb

  required.sort(priority_sort)

  return required


# find the first input image ... this will be used as "this"
def find_first_input_image(op, required):
  found = False
  for prop in required:
    flags = op.get_argument_flags(prop.name)
    if not flags & Vips.ArgumentFlags.INPUT:
      continue
    if GObject.type_is_a(vips_type_image, prop.value_type):
      found = True
      break

  if not found:
    return None

  return prop


# find the first output arg ... this will be used as the result
def find_first_output(op, required):
  found = False
  for prop in required:
    flags = op.get_argument_flags(prop.name)
    if not flags & Vips.ArgumentFlags.OUTPUT:
      continue
    found = True
    break

  if not found:
    return None

  return prop


def cppize(name):
  return re.sub('-', '_', name)


def upper_camelcase(name):
  if not name:
    return ''
  name = cppize(name)
  return ''.join(c for c in name.title() if not c.isspace() and c != '_')


def lower_camelcase(name):
  name = cppize(name)
  parts = name.split('_')
  return parts[0] + upper_camelcase(''.join(parts[1:]))


def gen_params(op, required):
  args = [];
  for prop in required:
    arg = lower_camelcase(prop.name) + ' '
    flags = op.get_argument_flags(prop.name)
    if flags & Vips.ArgumentFlags.OUTPUT:
      arg += '*'
    arg += get_type(prop)
    args.append(arg)
  args.append('opts ...OptionFunc')
  return ', '.join(args)


def gen_operation(cls):
  op = Vips.Operation.new(cls.name)
  gtype = Vips.type_find("VipsOperation", cls.name)
  nickname = Vips.nickname_find(gtype)
  all_required = find_required(op)

  result = find_first_output(op, all_required)
  this = find_first_input_image(op, all_required)
  this_part = ''
  this_ref = ''

  # shallow copy
  required = all_required[:]
  if result != None:
    required.remove(result)
  if this != None:
    required.remove(this)
    this_part = '(image *Image) '
    this_ref = 'image.'

  output = ''
  go_name = upper_camelcase(nickname)
  output += '// %s executes the \'%s\' operation\n' % (go_name, nickname)
  output += '// (see %s at http://www.vips.ecs.soton.ac.uk/supported/current/doc/html/libvips/func-list.html)\n' % nickname
  output += 'func %s%s(%s)' % (this_part, go_name, gen_params(op, required))
  if result != None:
    output += ' %s' % go_types[result.value_type.name]
  output += ' {\n'
  if result != None:
    output += '\tvar %s %s\n' % (lower_camelcase(result.name), get_type(result))
  output += '\toptions := NewOptions(opts...).With(\n'

  options = []
  source_image = None
  for prop in all_required:
    method_name = get_options_method_name(prop) + 'Input'
    arg_name = ''
    if prop == this:
      arg_name = 'image'
      source_image = arg_name
    else:
      flags = op.get_argument_flags(prop.name)
      arg_name = lower_camelcase(prop.name)
      if flags & Vips.ArgumentFlags.OUTPUT:
        method_name = get_options_method_name(prop) + 'Output'
        if prop == result:
          arg_name = '&' + arg_name
      if GObject.type_is_a(param_enum, prop):
        arg_name = 'int(%s)' % arg_name
    options.append('\t\t%s("%s", %s),\n' % (method_name, prop.name, arg_name))
  output += ''.join(options)

  output += '\t)\n'

  output += '\tvipsCall("%s", options)\n' % nickname
  # if this_ref:
  #   output += '\t%sLogCallEvent("%s", options)\n' % (this_ref, nickname)
  # elif result != None and get_type(result) == '*Image':
  if result != None and get_type(result) == '*Image':
    if source_image != None:
      output += '\t%s.CopyEvents(%s.callEvents)\n' % (lower_camelcase(result.name), source_image)
    output += '\t%s.LogCallEvent("%s", options)\n' % (lower_camelcase(result.name), nickname)

  if result != None:
    output += '\treturn %s\n' % lower_camelcase(result.name)
  output += '}'
  return output


# we have a few synonyms ... don't generate twice
generated = {}


def find_class_methods(cls):
  methods = []
  skipped = []
  if not cls.is_abstract():
    gtype = Vips.type_find("VipsOperation", cls.name)
    nickname = Vips.nickname_find(gtype)
    if not nickname in generated:
      try:
        methods.append(gen_operation(cls))
        generated[nickname] = True
      except Exception as e:
        skipped.append('// Unsupported: %s: %s' % (nickname, str(e)))
  if len(cls.children) > 0:
    for child in cls.children:
      m, s = find_class_methods(child)
      methods.extend(m)
      skipped.extend(s)
  return methods, skipped


def generate_file():
  methods, skipped = find_class_methods(vips_type_operation)
  methods.sort()
  skipped.sort()
  output = '%s\n\n' % preamble
  if len(skipped) > 0:
    output += '%s\n\n' % '\n'.join(skipped)
  output += '\n\n'.join(methods)
  print(output)


if __name__ == '__main__':
  generate_file()