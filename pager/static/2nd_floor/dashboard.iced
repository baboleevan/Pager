_ = require 'underscore'

adminfy = require './adminfy'

module.exports = (users) ->
  adminfy ->
    cumulative = total: 0, registred: 0, invited: 0
    cumulative_users =
      for [created, total, registred, invited] in users
        cumulative.total += total
        cumulative.registred += registred
        cumulative.invited += invited
        [created, cumulative.total, cumulative.registred, cumulative.invited]

    google.load "visualization", "1", packages: ["corechart"], callback: ->
      users.unshift ['날짜', '전체', '가입', '미가입']
      data = google.visualization.arrayToDataTable users

      options = {}

      users_chart = new google.visualization.LineChart $('.chart-users')[0]
      users_chart.draw data, options

      cumulative_users.unshift ['날짜', '전체', '가입', '미가입']
      cumulative_data = google.visualization.arrayToDataTable cumulative_users

      options = {}

      cumulative_users_chart = new google.visualization.LineChart $('.chart-cumulative-users')[0]
      cumulative_users_chart.draw cumulative_data, options

