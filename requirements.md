# Requirements

## Overview

The platform is a Patient – Doctor relations application (further PDR) that allows the Dr. to see what the patient is doing on the application. The patient on his side gets tasks and missions to improve his health.

As part of this project we would like to help the Dr. to decide which patient require attention, priorities the patients and help them understand what made the system decide on the priority. This new service that will allow us to run ML models to identify potentials areas that require the Dr. attention. You will get a sample data set to give you a better understanding of the platform income data and few rules to start with.

You are required to plan and build the MVP, a rule-based service that will allow us to scan the data every 5 minutes and identify situations that require the Dr. attention.

The expected delivery is to build a service that will connect to a Data base – you get to choose the technologies and databases that will best fit this need. The service needs to be live on GCP (Google cloud), the code hosted on Git and have a simple pipeline for deployment. 

**Minimal requirements for the service logic:**

1. This service will read the data every 5 minutes and will verify if one or more of the rules apply
2. If the rule apply write the message to the DB in a dedicated table

**Nice to haves:**

1. Visualization of the alerts on a web page.
2. Allow to easily add more rules

## Details

1. PDR produces the following records (representing user actions):
   - user id
   - timestamp (datetime)
   - type - e.g., steps, medication, mind, PRO, water
   - description - additional details of the event; the format and the interpretation depends on the type of the event
2. The user action records are written to the `user actions` database
3. The 'user actions' database is scanned every 5 minutes, and rules are evaluated
4. For every matching rule, the service writes an alert record to the `alerts` database. Structure of an alert is:
   - priority (int > 0)
   - rule id
   - message - a human readable description of the alert

## Questions

**Functional:**

1. Should I assume that the records illustrated by the sample dataset (in user actions tab) are part of the existing application functionality?
   - If they are, - what is the exact schema/format of the data? (for instance, the 'description' field looks like a textual representation of possibly more complex structure, unless its written as text by the app, and therefore would have to be parsed by my service)
   - Otherwise (meaning, that's a new functionality hence the format is subject to the design decision) - can I decide on the format of the records or should I accept the format is given (i.e. description is a text that has to be parsed?)
2. Who writes the records to the 'user actions' database? Can I assume that the writing part is out of scope (i.e. responsibility of a different service)?
3. What should be written to the alerts database in addition to the message? I assume {patient id, priority, rule id, extended attrs}?
4. What is the relationship between a rule and priority value? Is each rule assigned a fixed priority value?
5. Would the consumer services/applications directly read alerts from the alerts database?

**Non-Functional:**

The following NFRs might be irrelevant to the assignment, however I prefer to ask them as these would be important in case of a real project.

1. Expected/peak number of users?
2. User actions' expected write rate? Peak rate?
3. What is the required processing latency? That is, from the moment the action is written to the actions DB to the moment a corresponding alert appears in the alerts DB?
4. For how long should the user actions and alerts be kept in the service's database?
5. Security requirements/constraints?
