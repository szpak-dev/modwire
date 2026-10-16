# Check a polyglot project

This tutorial builds a tiny system with a Python backend and a TypeScript frontend.
Both use the same architecture convention: a bounded context contains a feature,
and the feature contains directional layers.

You will initialize Modwire, observe a real backward dependency, repair it, and run
the same architecture checks for both languages.

## Install the required runtimes

Modwire requires Python 3.12 or newer:

```console
python -m pip install modwire
```

The Python extractor runs with Modwire. TypeScript extraction also requires a
supported Node.js version on `PATH`. See
[Language support and limits](../reference/language-support.md) for the exact runtime
contract.

## Create the source tree

Create an empty project and enter it:

```console
mkdir modwire-example
cd modwire-example
```

Create this source tree:

```text
src/
├── backend/
│   └── sales/
│       └── orders/
│           ├── application/
│           │   └── totals.py
│           └── domain/
│               └── tax.py
└── frontend/
    └── commerce/
        └── checkout/
            └── page/
                └── total.ts
```

Put this application function in
`src/backend/sales/orders/application/totals.py`:

```{literalinclude} ../_examples/tutorial/src/backend/sales/orders/application/totals.py
:language: python
```

Put this deliberately invalid dependency in
`src/backend/sales/orders/domain/tax.py`:

```{literalinclude} ../_examples/tutorial/src/backend/sales/orders/domain/tax.py
:language: python
```

The domain layer now imports the application layer. The configured order will run
from entry point toward core, so this dependency points backward.

Add the TypeScript page at
`src/frontend/commerce/checkout/page/total.ts`:

```{literalinclude} ../_examples/tutorial/src/frontend/commerce/checkout/page/total.ts
:language: typescript
```

The source tree separates language-specific code under `backend` and `frontend`.
`sales` and `commerce` are bounded contexts, `orders` and `checkout` are features,
and the final directory in each path is a layer.

## Initialize and configure Modwire

Run:

```console
modwire init
```

Modwire creates `.modwire/architecture.yaml` and short project guidance. Existing
files are preserved unless you explicitly pass `--force`.

Replace the generated `.modwire/architecture.yaml` with:

```{literalinclude} ../_examples/tutorial/.modwire/architecture.yaml
:language: yaml
```

The two realms have separate layer vocabularies. Their boundary rules close bounded
contexts and features by default, while `backward-flow` checks the declared layer
direction. The shape realm permits this tutorial's small functions without
introducing an unrelated failure.

## Observe the backward dependency

Run the Python report:

```console
modwire report --language python --summary
```

The command exits with status `1`. Its public output identifies the rule and the
complete dependency path:

```text
Flow violations:
  - [analyzer:backend:backward-flow] src/backend/sales/orders/domain/tax.py
    points backward to src/backend/sales/orders/application/totals.py
    src/backend/sales/orders/domain/tax.py ->
    src/backend/sales/orders/application/totals.py
```

This is an architecture failure rather than a style score: a core domain file
depends on an outer application layer.

## Repair the dependency

Remove the domain layer's dependency on the application layer by making `tax`
receive the subtotal as an input. Replace `src/backend/sales/orders/domain/tax.py`
with:

```{literalinclude} ../_examples/tutorial-repair/tax.py
:language: python
```

Run the report again:

```console
modwire report --language python --summary
```

The command exits with status `0` and ends with:

```text
Architecture checks passed.
```

## Check the other language

Run the TypeScript report against the same configuration:

```console
modwire report --language typescript --summary
```

It also exits with status `0` and ends with `Architecture checks passed.` The report
runs are separate, but their bounded-context, feature, layer, and rule vocabulary is
shared.

You now have the smallest useful Modwire loop: express an architecture, observe the
exact dependency that violates it, repair the source, and keep the decision
executable for every supported language in the repository.
