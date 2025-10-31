# Infrastructure: ContractType Configuration

**Namespace:** `Infrastructure.Persistence.Configurations.DayaDarou.Hr`  
**File:** `ContractTypeConfiguration.cs`  
**Database Table:** `[Hr].[ContractTypes]`  
**Entity:** `Domain.Entity.DayaDarou.Hr.Definitions.ContractType`  

---

| Property | Configuration | Notes |
|-----------|----------------|-------|
| `ContractTypeId` | `HasKey()` | Defines the primary key. |
| `ContractTypeCode` | `IsRequired()` | Must be unique and non-null. |
| `ContractTypeName` | `HasMaxLength(100).IsUnicode(true).IsRequired()` | NVARCHAR(100), required, unique. |
| `ContractPrintName` | `HasMaxLength(100).IsUnicode(false).IsRequired()` | VARCHAR(100), required. |
| `ContractSortId` | *(Optional, commented out in EF config)* | Default set to 0 in SQL script. |