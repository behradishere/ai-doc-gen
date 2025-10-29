# Domain Model – ContractType

The **ContractType** entity represents the types of contracts that employees can have.

### Table And Schema
```csharp
[Table("ContractTypes", Schema = "Hr")]
```

### Entity Definition:
```csharp
public class ContractType
{
    public int ContractTypeId { get; set; }
    public string ContractTypeCode { get; set; }
    public string ContractTypeName { get; set; }
    public string ContractPrintName { get; set; }
    public int ContractSortId { get; set; }
}
```
### RELATIONS
```csharp
    public virtual ICollection<Employee> Employees { get; set; } = new List<Employee>();
    public virtual ICollection<Order> Orders { get; set; } = new List<Order>();
    public virtual ICollection<PayRoll> PayRolls { get; set; } = new List<PayRoll>();
```