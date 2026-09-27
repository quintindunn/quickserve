---
description: Guidelines for contributing to QuickServe
---

# Contribution Guidelines

{% hint style="info" %}
Last Updated: 09/27/2026
{% endhint %}

**This page is currently a placeholder; Guidelines will be added here in the future.**

### Modules

#### Grandfather Clause

While not guaranteed, updates to modules that have already been accepted will be held to the standards set when they were accepted.

#### Module Name

Module names must be concise and formatted in [kebab-case](https://developer.mozilla.org/en-US/docs/Glossary/Kebab_case).

> **Kebab case** is a way of writing phrases without spaces, where spaces are replaced with hyphens `-`, and the words are typically all lower case. The name comes from the similarity of the words to meat on a kebab skewer. It's often stylized as "kebab-case" to remind the reader of its appearance.

Accepted Examples:

```
minecraft-vanilla
satisfactory-vanilla
terraria-tmodloader
```

Rejected Examples:

```
Minecraft Vanilla     # Module name has spaces and is not lowercase
super-cool-module     # Module name is not descriptive
Satisfactory-Vanilla  # Module name is not lowercase
```

#### Module Version

Module versions must follow the [SemVer 2.0.0](https://semver.org/) styling.

> Given a version number MAJOR.MINOR.PATCH, increment the:
>
> 1. MAJOR version when you make incompatible API changes
> 2. MINOR version when you add functionality in a backward compatible manner
> 3. PATCH version when you make backward compatible bug fixes
>
> Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format.

Accepted Examples:

```
0.0.1
0.1.0
1.0.0
2.4.1
1.0.0-beta
```

Rejected Examples:

```
1              # Version must have major, minor, and patch
1.2            # Version is missing patch
v1.2.3         # Version `v` isn't part of SemVer 2.0.0
1.2.3.4.       # Version has too many numeric components
1.2.3-alpha_1  # Version does not allow `_` in identifiers
```

[Here](https://regexr.com/39s32) is a useful tool by gskinner on [regexr.com](https://regexr.com).
