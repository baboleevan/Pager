_ = require 'underscore'

log = _.bind console.log, console
error = _.bind console.error, console

module.exports = {log, error}
