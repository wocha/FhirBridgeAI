# FHIR Data Type Patterns (Pydantic)

Always use these patterns when constructing complex FHIR resources in Pydantic.

## HumanName

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class HumanName(BaseModel):
    use: Optional[str] = None # e.g., 'official', 'usual'
    family: Optional[str] = None
    given: Optional[List[str]] = None
    prefix: Optional[List[str]] = None
    suffix: Optional[List[str]] = None
```

## Identifier

Crucial for ISiK (e.g., Versichertennummer).

```python
from typing import Optional
from pydantic import BaseModel

class Identifier(BaseModel):
    use: Optional[str] = None # e.g., 'usual', 'official'
    system: Optional[str] = None # The namespace/URL
    value: Optional[str] = None
```

## Coding & CodeableConcept

Used for ICD-10, SNOMED, etc.

```python
from typing import List, Optional
from pydantic import BaseModel

class Coding(BaseModel):
    system: Optional[str] = None
    version: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None

class CodeableConcept(BaseModel):
    coding: Optional[List[Coding]] = None
    text: Optional[str] = None
```

## Reference

Used to link resources.

```python
from typing import Optional
from pydantic import BaseModel

class Reference(BaseModel):
    reference: Optional[str] = None # e.g. "Patient/123"
    type: Optional[str] = None
    display: Optional[str] = None
```

## Extension

Used for ISiK/German profile extensions (e.g., Stadtteil, GeschlechtAdministrativ).

```python
from typing import Optional
from pydantic import BaseModel

class Extension(BaseModel):
    url: str
    valueString: Optional[str] = None
    valueCode: Optional[str] = None
    valueCoding: Optional["Coding"] = None
    valueBoolean: Optional[bool] = None
```

## Meta

**Critical for ISiK**: Without `meta.profile`, a resource is not identifiable as ISiK-conformant.

```python
from typing import List, Optional
from pydantic import BaseModel

class Meta(BaseModel):
    profile: Optional[List[str]] = None
    versionId: Optional[str] = None
    lastUpdated: Optional[str] = None
```

## ContactPoint

Must-Support on `Patient.telecom` in ISiK.

```python
from typing import Optional
from pydantic import BaseModel

class ContactPoint(BaseModel):
    system: Optional[str] = None  # 'phone'|'email'|'fax'
    value: Optional[str] = None
    use: Optional[str] = None     # 'home'|'work'|'mobile'
    rank: Optional[int] = None
```

## ⚠️ ConfigDict Reminder

When using `Field(alias="...")` (e.g., `class_` → `"class"` on Encounter), you **must** add:

```python
from pydantic import ConfigDict

class MyResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
```

Without this, Python-side instantiation via keyword (`class_=...`) will fail.
