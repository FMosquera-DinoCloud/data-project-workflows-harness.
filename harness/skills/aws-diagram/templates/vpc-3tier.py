#!/usr/bin/env python
"""
Template: VPC de 3 capas (ALB → ECS → RDS Multi-AZ) en subnets públicas/privadas.

Correr SIEMPRE con el python del venv de la skill:
    ~/.dino/aws-diagram/.venv/bin/python vpc-3tier.py

Variables de entorno:
    OUTDIR=docs/diagrams   (default)

Nota: las IPs y CIDRs son de ejemplo. Nunca pongas rangos, account IDs ni
nombres de cliente reales en un diagrama sin autorización escrita.
"""

import os

from diagrams.aws.compute import ECS
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB, InternetGateway, NATGateway, Route53
from diagrams.aws.security import WAF

from aws_diagram_theme import cluster, diagram, edge

OUTDIR = os.environ.get("OUTDIR", "docs/diagrams")

with diagram("VPC 3 capas", outdir=OUTDIR, direction="LR"):
    dns = Route53("Route 53")
    waf = WAF("WAF")

    with cluster("VPC 10.0.0.0/16"):
        igw = InternetGateway("Internet Gateway")

        with cluster("Subnets públicas · 2 AZ"):
            alb = ELB("ALB")
            nat = NATGateway("NAT Gateway")

        with cluster("Subnets privadas · app"):
            app = [ECS("ECS Fargate\naz-a"), ECS("ECS Fargate\naz-b")]

        with cluster("Subnets privadas · datos"):
            db_primary = RDS("RDS primary")
            db_standby = RDS("RDS standby")

    dns >> edge("A record") >> waf >> edge("HTTPS 443") >> igw >> edge("ingress") >> alb
    alb >> edge("HTTP 8080") >> app
    app >> edge("TLS 5432") >> db_primary
    db_primary - edge("réplica síncrona", style="dashed") - db_standby
    app >> edge("egress", style="dotted") >> nat
