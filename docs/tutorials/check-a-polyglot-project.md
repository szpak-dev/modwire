# Check a polyglot project

This tutorial builds a tiny system with a Python backend and a TypeScript frontend.
Both use the same architecture convention: a bounded context contains a feature,
and the feature contains a layer.

You will initialize Modwire, observe a real shape violation, fix it, and run the
same architecture checks for both languages.

## Install the required runtimes

Modwire requires Python 3.12 or newer:

```console
python -m pip install modwire
```

The Python extractor runs with Modwire. TypeScript extraction also requires Node.js
on `PATH`. PHP extraction requires PHP on `PATH` when you use it.

## Create the source tree

Create an empty project and enter it:

```console
mkdir modwire-example
cd modwire-example
```

Create an `orders` feature inside the backend's `sales` bounded context:

```text
src/
└── backend/
    └── sales/
        └── orders/
            └── application/
                └── totals.py
```

Put two top-level functions in
`src/backend/sales/orders/application/totals.py`:

```python
def subtotal() -> int:
    return 100


def tax() -> int:
    return 23
```

Create a `checkout` feature inside the frontend's `commerce` bounded context:

```text
src/
└── frontend/
    └── commerce/
        └── checkout/
            └── page/
                └── total.ts
```

Put one function in `src/frontend/commerce/checkout/page/total.ts`:

```typescript
export function total(): number {
  return 123;
}
```

The source tree separates language-specific code under `backend` and `frontend`.
`sales` and `commerce` are bounded contexts, `orders` and `checkout` are features,
and `application` and `page` are layers. The configuration below defines dependency
analysis realms named `backend` and `frontend`, each with its own module tag and layer
order.

## Initialize Modwire

Run:

```console
modwire init
```

Modwire creates `.modwire/architecture.yaml` and short project guidance. Existing
files are preserved unless you explicitly pass `--force`.

Replace the generated `.modwire/architecture.yaml` with the tutorial configuration:

```yaml
excluded_patterns:
  - .git/**
  - .modwire/**

boundaries:
  tags:
    - {name: backend-context, match: "src/backend/*"}
    - {name: backend-feature, match: "src/backend/*/*"}
    - {name: backend-api, match: "src/backend/*/*/api"}
    - {name: backend-application, match: "src/backend/*/*/application"}
    - {name: backend-infrastructure, match: "src/backend/*/*/infrastructure"}
    - {name: backend-domain, match: "src/backend/*/*/domain"}
    - {name: frontend-context, match: "src/frontend/*"}
    - {name: frontend-feature, match: "src/frontend/*/*"}
    - {name: frontend-page, match: "src/frontend/*/*/page"}
    - {name: frontend-state, match: "src/frontend/*/*/state"}
    - {name: frontend-component, match: "src/frontend/*/*/component"}

  rules:
    - {realm: backend, source: backend-context, disallow: [backend-context], allow_same_match: true}
    - {realm: backend, source: backend-feature, disallow: [backend-feature], allow_same_match: true}
    - {realm: frontend, source: frontend-context, disallow: [frontend-context], allow_same_match: true}
    - {realm: frontend, source: frontend-feature, disallow: [frontend-feature], allow_same_match: true}

  flow:
    realms:
      - name: backend
        module_tag: backend-feature
        layers: [backend-api, backend-application, backend-infrastructure, backend-domain]
      - name: frontend
        module_tag: frontend-feature
        layers: [frontend-page, frontend-state, frontend-component]
    analyzers: [module-boundaries, backward-flow, no-cycles, no-reentry]

shape:
  realms:
    - name: source
      match: src
      shape:
        max_functions_per_file: 1
        max_variables_per_file: 0
```

The configuration names each architectural level independently. Its boundary rules
close contexts and features by default. Its shape rules limit a source file to one
top-level function and no module-scope variables.

## Let the rule fail

Run the Python report:

```console
modwire report --language python --summary
```

The command exits with status `1`. Its shape report names
`max_functions_per_file` and
`src/backend/sales/orders/application/totals.py`. That file contains two top-level
functions while the configured limit is one.

This failure is useful. The architecture rule points to a source-level decision,
not a generic score.

Move `tax` into `src/backend/sales/orders/application/tax.py`, leaving one function
in each file. Run the report again:

```console
modwire report --language python --summary
```

The command now exits with status `0` and ends with:

```text
Architecture checks passed.
```

## Check the other language

Run the TypeScript report against the same configuration:

```console
modwire report --language typescript --summary
```

It also ends with `Architecture checks passed.` The two report runs are separate,
but their tags, feature boundaries, layers, and shape vocabulary are shared.

You now have the smallest useful Modwire loop: express architecture in the source
tree, map it with configuration, run a language report, and change the code or the
rule deliberately when they disagree.
