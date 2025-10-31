
---

#### `📦 BoundedContext/HR/ContractType/20-Application.md`


# Application Layer – ContractType

## Commands

### CreateContractTypeCommand
- **Purpose**: Creates a new contract type.
- **Validation**: Ensures the `ContractTypeCode` is unique and NotEmpty also checks `ContractTypeName` length and NotEmpty.
- **Handler**: Validates input, creates the entity, and returns the new `ContractTypeId`.

```csharp
public class CreateContractTypeCommand : IRequest<int>
{
    public int ContractTypeCode { get; set; }
    public string ContractTypeName { get; set; }
    public int ContractSortId { get; set; }
}
```

### DeleteContractTypeCommand
- **Purpose**: Deletes a contract type.
- **Validation**: Ensures the `ContractTypeId` is available.
- **Handler**: Validates input, Deletes the entity, and returns a success meessage.

```csharp
public class DeleteContractTypeCommand : IRequest<Result<string>>
{
    public int ContractTypeId { get; set; }
}
```

### UpdateContractTypeCommand
- **Purpose**: Updates a contract type.
- **Validation**: Ensures the `ContractTypeId` is available and checks `ContractTypeName` length.
- **Handler**: Validates input, Updates the entity, and returns a success meessage.

```csharp
public class UpdateContractTypeCommand : IRequest<Result<string>>
    {
        public int ContractTypeId { get; set; }
        public int? ContractTypeCode { get; set; }
        public string ContractTypeName { get; set; }
        public int? ContractSortId { get; set; }
    }
```