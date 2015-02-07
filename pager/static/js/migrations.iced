_ = require 'underscore'
locache = require 'locache'

cleanup_local_storage = ->
  # due to chagne from raw localstroage to locache library
  # locache library uses prefix ___locache___
  # so transfer data to locache
  for key in _.filter(_.keys(localStorage), (k) -> /^user\./.test k)
    locache.set key, JSON.parse localStorage.getItem key
    localStorage.removeItem key

module.exports = (callback) ->
  cleanup_local_storage()
  callback()