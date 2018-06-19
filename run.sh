#!/bin/bash

export FLASK_APP=shadow

#production or development
export FLASK_ENV=development

flask $@