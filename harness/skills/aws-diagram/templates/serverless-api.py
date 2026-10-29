#!/usr/bin/env python
"""
Template: API serverless (API Gateway → Lambda → DynamoDB) con auth Cognito.

Correr SIEMPRE con el python del venv de la skill:
    ~/.dino/aws-diagram/.venv/bin/python serverless-api.py

Variables de entorno:
    OUTDIR=docs/diagrams   (default)
"""

import os

from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.management import Cloudwatch
from diagrams.aws.network import APIGateway, CloudFront
from diagrams.aws.security import Cognito
from diagrams.aws.storage import S3
from diagrams.onprem.client import Users

from aws_diagram_theme import cluster, diagram, edge

OUTDIR = os.environ.get("OUTDIR", "docs/diagrams")

with diagram("API Serverless", outdir=OUTDIR, direction="LR"):
    users = Users("Clientes")
    cdn = CloudFront("CloudFront")
    spa = S3("SPA estática")

    with cluster("Cuenta AWS · prod"):
        auth = Cognito("Cognito\nUser Pool")
        api = APIGateway("API Gateway\nHTTP API")
        fn = Lambda("Handlers")
        table = Dynamodb("DynamoDB\non-demand")
        logs = Cloudwatch("CloudWatch\nLogs + Alarms")

    users >> edge("HTTPS") >> cdn >> edge("origen") >> spa
    users >> edge("REST · JWT") >> api
    api >> edge("authorizer") >> auth
    api >> edge("invoke") >> fn
    fn >> edge("GetItem / PutItem") >> table
    fn >> edge("logs · métricas") >> logs
