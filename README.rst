Hospital Management
===================

`hr_hospital` is an Odoo module for basic hospital operations.

Features
--------

* patient and doctor profiles
* visit planning and visit history
* hierarchical disease classifier
* doctor assignment history
* dashboard, kanban views and PDF reports
* Ukrainian translations

Access model
------------

The module defines a hospital role chain:

* Patient
* Intern
* Doctor
* Manager
* Administrator

Visit access is scoped by these roles and by record rules.

Reports
-------

The module includes a printed doctor report and disease statistics reports.

Development notes
-----------------

The module depends on ``base`` and ``hr``.
