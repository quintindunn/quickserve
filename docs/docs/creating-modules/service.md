---
description: The entry point for your module
---

# Service

All QuickServe modules have a core class named `Service`. When QuickServe loads your module, it will instantiate this class.

### Contract

Modules in QuickServe must satisfy a "contract". The current requirements to satisfy the contract are the following:

#### Module (Class) Attributes:

Class Attributes,  also known as Module Attributes, that are required.

***

`NAME` - The internal name of your module. [Related Guidelines](../contributing/contribution-guidelines.md#module-name)

```python
NAME: str = "my-module-name
```

***

`VERSION` - The version of your module. [Related Guidelines](../contributing/contribution-guidelines.md#module-version)

```python
VERSION: str = "1.0.0"
```

***

`QUICKSERVE_VERSION` - The minimum version of QuickServe supported by your module.

```python
QUICKSERVE_VERSION: str = "0.0.1"
```

***

`PAGES` - A list of registered pages within your module.

```python
PAGES: list[str] = ["about", "create", "start", "filesystem"]
```

#### Module (Class) Methods

Class Methods,  also known as Module Methods, that are required.

{% hint style="info" %}
```python
PageResult: TypeAlias = str | tuple[str, dict[str, Any]]
```
{% endhint %}

***

`about` - The method that renders your module's about page.

```python
def about(self, *args: Any, **kwargs: Any) -> PageResult: ...
```

***

`create` - The method that creates an instance of your module.

```python
def create(self, *args: Any, **kwargs: Any) -> PageResult: ...
```
