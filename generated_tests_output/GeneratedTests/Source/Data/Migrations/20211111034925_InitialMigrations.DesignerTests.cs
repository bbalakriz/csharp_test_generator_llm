To generate a complete and runnable NUnit test class for the `InitialMigrations` class using NUnit, we need to create a test fixture that sets up an in-memory context of `TodoDbContext`, and then tests the migration configuration. Below is the generated code:

```csharp
using System;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Migrations;
using NUnit.Framework;

namespace GeneratedTests
{
    [TestFixture]
    public class InitialMigrationsTests
    {
        private TodoDbContext _context;

        // Setup method to create an in-memory context for testing
        [SetUp]
        public void SetUp()
        {
            var options = new DbContextOptionsBuilder<TodoDbContext>()
                .UseInMemoryDatabase(databaseName: "TestDb")
                .Options;
            _context = new TodoDbContext(options);
        }

        // Test that the migration configuration is correct
        [Test]
        public void Migrations_Configuration_Should_Be_Correct()
        {
            // Arrange - The context is already set up with in-memory database

            // Act - Build target model and validate it
            _context.Database.EnsureCreated();
            var modelBuilder = new ModelBuilder(new DbContextOptions<TodoDbContext>());
            modelBuilder.ApplyConfiguration(new InitialMigrations());

            // Assert - Check the properties of the entity to ensure they match the expected configuration
            var todoItemEntityTypeBuilder = modelBuilder.Model.GetEntityTypes().Single(e => e.Name == "TodoItem");

            // Property 'Id'
            Assert.AreEqual("int", todoItemEntityTypeBuilder.FindProperty("Id").ClrType.Name);
            Assert.IsTrue(todoItemEntityTypeBuilder.FindProperty("Id").IsPrimaryKey());

            // Property 'IsCompleted'
            Assert.AreEqual("bit", todoItemEntityTypeBuilder.FindProperty("IsCompleted").ClrType.Name);

            // Property 'PeriodStart'
            var periodStartProperty = todoItemEntityTypeBuilder.FindProperty("PeriodStart");
            Assert.AreEqual("datetime2", periodStartProperty.ClrType.Name);
            Assert.IsTrue(periodStartProperty.ValueGenerated.HasFlag(CoreValueGenerationStrategy.OnAddOrUpdate));

            // Property 'PeriodEnd'
            var periodEndProperty = todoItemEntityTypeBuilder.FindProperty("PeriodEnd");
            Assert.AreEqual("datetime2", periodEndProperty.ClrType.Name);
            Assert.IsTrue(periodEndProperty.ValueGenerated.HasFlag(CoreValueGenerationStrategy.OnAddOrUpdate));

            // Property 'Title'
            Assert.AreEqual("nvarchar(max)", todoItemEntityTypeBuilder.FindProperty("Title").ClrType.FullName);

            // Check if the table is correctly named and temporal
            var tableName = todoItemEntityTypeBuilder.GetTableName();
            Assert.AreEqual("TodoItems", tableName);
            var tableTemporalConfig = todoItemEntityTypeBuilder.TemporalConfiguration;
            Assert.IsNotNull(tableTemporalConfig);
        }
    }

    public class TodoDbContext : DbContext
    {
        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.ApplyConfiguration(new InitialMigrations());
        }
    }
}
```

### Explanation:
1. **Namespace and Class Name**: The test class is named `InitialMigrationsTests` in the namespace `GeneratedTests`.
2. **SetUp Method**: This method sets up an in-memory database context for testing purposes.
3. **Test Method**: The `[Test]` attribute marks this as a test case. It ensures that the migration configuration matches the expected properties and configurations.

### Notes:
- The `TodoDbContext` class is included to ensure that the migrations can be applied within a valid context.
- The test checks various aspects of the entity (`TodoItem`) such as its properties, primary key, value generation strategy, and table configuration.
- You may need to adjust the property types based on actual database configurations if they differ.

This setup should provide a good foundation for testing migrations in an NUnit environment.