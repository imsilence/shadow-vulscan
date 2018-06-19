@echo off

set FLASK_APP=shadow

::production or development
set FLASK_ENV=development

flask %*