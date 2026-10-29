#!/usr/bin/env python3
"""Precios de AWS desde la Price List API: la única fuente para un precio que va a un documento o a un cliente.

Uso:
  aws_price.py <service-code> [campo=valor ...] [--region us-east-1] [--profile <perfil>] [--grep <texto>]
Ejemplos:
  aws_price.py AmazonEC2 instanceType=g4dn.xlarge operatingSystem=Linux tenancy=Shared preInstalledSw=NA capacitystatus=Used
  aws_price.py AmazonSageMaker instanceName=ml.g4dn.xlarge --grep AsyncInf
  aws_price.py transcribe --grep TranscribeAudio
  aws_price.py AmazonECS instanceType=g4dn.xlarge            (tarifa de gestión de ECS Managed Instances)
Imprime por dimensión: usagetype, descripción, precio, unidad, escalón (beginRange-endRange) y fecha de vigencia.
Los escalones salen tal como los publica AWS: si no hay escalones, el rango es 0 - Inf.
"""
import json
import subprocess
import sys


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        raise SystemExit(__doc__)
    service, region, profile, grep, filters = args[0], "us-east-1", None, None, []
    i = 1
    while i < len(args):
        a = args[i]
        if a in ("--region", "--profile", "--grep"):
            val = args[i + 1]
            region, profile, grep = (val, profile, grep) if a == "--region" else (region, val, grep) if a == "--profile" else (region, profile, val)
            i += 2
            continue
        field, _, value = a.partition("=")
        filters.append(f"Type=TERM_MATCH,Field={field},Value={value}")
        i += 1
    filters.append(f"Type=TERM_MATCH,Field=regionCode,Value={region}")
    cmd = ["aws", "pricing", "get-products", "--service-code", service, "--region", "us-east-1",
           "--filters", *filters, "--output", "json"]
    if profile:
        cmd += ["--profile", profile]
    rows, token = [], None
    while True:
        r = subprocess.run(cmd + (["--next-token", token] if token else []), capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stderr.strip()[-500:])
        data = json.loads(r.stdout)
        for item in data.get("PriceList", []):
            p = json.loads(item)
            ut = p["product"]["attributes"].get("usagetype", "")
            for term in p["terms"].get("OnDemand", {}).values():
                for d in term["priceDimensions"].values():
                    line = (f"{ut} | {d['description'][:90]} | {d['pricePerUnit'].get('USD')} {d['unit']} | "
                            f"{d.get('beginRange')} - {d.get('endRange')} | desde {term['effectiveDate'][:10]}")
                    if not grep or grep.lower() in line.lower():
                        rows.append(line)
        token = data.get("NextToken")
        if not token:
            break
    print("\n".join(sorted(rows)) if rows else "sin resultados (revisar service-code y filtros)")
    print(f"\nFuente: AWS Price List API, {service}, {region}.")


if __name__ == "__main__":
    main()
