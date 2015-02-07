methods = ['observable', 'observableArray'];
for method in methods
  do (method) ->
    ko[method + 'Presist'] = (initialValue, {key}) ->
      if not key?
        throw Error "ko.#{method}Presist needs {key} argument"
      initialValue = locache.get(key) ? initialValue
      observable = ko[method] initialValue
      observable.subscribe (value) ->
        locache.set key, value
      observable
