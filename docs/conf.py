from recommonmark.parser import CommonMarkParser
extensions = ['myst_parser']
source_parsers = {
'.md': CommonMarkParser,
}

source_suffix = ['.rst', '.md']
master_doc = 'index'
project = u'labscript-qc1'
