class Requirify
  @library:
    jquery: jQuery, underscore: _, knockout: ko, 'socket.io': io
    async: async, 'iced-coffee-script': {iced}, moment: moment
    hammer: {Hammer}, 'one-color': ONECOLOR, path: Path, raven: Raven
    locache: locache

  @local: {}

  @require = (name) =>
    module = @library[name]
    if module?
      return module
    module = @local[name]
    if not module?
      # if somebody call index.js then redefine module name.
      if basename(name) is 'index'
        return @require dirname name
      throw Error "Module #{name} dose not exist"
    # the module isnt initilized yet
    if module.init?
      init = module.init
      delete module.init
      init()
    if not module.initilized
      throw Error(
        "
        Module #{name} finish init() calling but not initilized yet.
        This means possible circular dependency occured.
        "
      )
    module.exports

  @has = (name) ->
    @library[name]? or @local[name]?

  @_regist = (module_name, module) ->
    @local[module_name] = module


norm_path = (path) ->
  result = []
  for dir in path.split '/'
    if dir in ['', '.']
      continue
    if dir is '..'
      # can clime up directory with deleting last elements,
      if result.length > 0 and _.last(result) isnt '..'
        result.pop()
        continue
    # if nothing happens just enlarge stack
    result.push dir
  result.join '/'

dirname = (path) ->
  path.split('/')[...-1].join '/'

basename = (path) ->
  _.last path.split('/')


window.require = Requirify.require


window.requirify = (filename, init) ->
  # trimming /index.* or extentions
  module_name = filename.replace /(\/index)?.[^.]*$/, ''
  mdoule_path = dirname filename
  # if module already registered simply pass it
  if Requirify.has module_name
    return
  module = {exports: {}, filename: filename, initilized: no}
  module.init = ->
    init(
      # require
      (name) ->
        if name[0] is '.'
          name = norm_path [mdoule_path, name].join '/'
        Requirify.require name
      module.exports, module
    )
    module.initilized = yes
  Requirify._regist module_name, module