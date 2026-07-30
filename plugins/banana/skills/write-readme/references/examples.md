# README Examples

Use these as behavior examples, not as copy sources.

## Value Proposition

Good:

```markdown
> Archive weekly WakaTime stats and publish SVG cards in your GitHub profile.
```

Bad:

```markdown
> A modern tool built with Node.js for developer productivity.
```

Why: the good version names the concrete job and output.

## Quick Start

Good:

````markdown
## Quick Start

```bash
npm install
npm run build
npm start
```

Open `http://localhost:3000`.
````

Bad:

```markdown
## Quick Start

Install dependencies and run the project.
```

Why: the good version is copy-pasteable and states the expected result.

## Unsupported Fact Handling

Good report note:

```markdown
Assumption: No package publication badge was added because this repository does
not contain evidence that the package is published to npm.
```

Bad README content:

```markdown
[![npm version](https://img.shields.io/npm/v/my-package.svg)](...)
```

Why: a local package name does not prove publication.

## Configuration Table

Good:

```markdown
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_BASE_URL` | Yes | none | Backend API origin used by the web app. |
```

Bad:

```markdown
Configure the app with the usual environment variables.
```

Why: config should be user-facing, concrete, and backed by files such as
`.env.example`, schemas, or existing docs.
