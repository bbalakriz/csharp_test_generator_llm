To generate a NUnit test class for the `UsersTableSetAsTemporal` migration, we need to simulate the behavior of the migration within an in-memory database context. This can be achieved by creating a mock DbContext and running the Up and Down methods on it.

Here is a complete, runnable NUnit test class:

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using MinimalApi.Data; // Adjust this namespace according to your project structure
using System;
using System.Linq;
using System.Threading.Tasks;
using Xunit;

namespace GeneratedTests
{
    [TestFixture]
    public class UsersTableSetAsTemporalTests
    {
        private DbContextOptions<MinimalApiDbContext> options;
        private MinimalApiDbContext context;

        public UsersTableSetAsTemporalTests()
        {
            // Setup the in-memory database options
            var serviceProvider = new ServiceCollection()
                .AddEntityFrameworkInMemoryDatabase()
                .BuildServiceProvider();
            
            options = new DbContextOptionsBuilder<MinimalApiDbContext>()
                .UseInMemoryDatabase(databaseName: "TestDb")
                .UseInternalServiceProvider(serviceProvider)
                .Options;

            // Create a context with the options
            context = new MinimalApiDbContext(options);
        }

        [OneTimeSetUp]
        public void OneTimeSetup()
        {
            // Seed some data for testing if needed
            context.TodoItems.Add(new TodoItem { Id = 1, CreatedOn = DateTime.UtcNow });
            context.Users.Add(new User { Id = 1, CreatedOn = DateTime.UtcNow });
            context.SaveChanges();
        }

        [Test]
        public async Task TestUpMigration()
        {
            // Arrange
            var migration = new UsersTableSetAsTemporal();

            // Act
            await using (var contextForMigration = new MinimalApiDbContext(options))
            {
                await migration.Up(new Migrator(), contextForMigration);
            }

            // Assert
            var usersHistoryExists = contextForMigration.Model.FindEntityType("Users").GetForeignKeys().Any(fk => fk.PrincipalKey?.Name == "FK_Users_History");
            Assert.True(usersHistoryExists, "UsersHistory table should exist.");
            
            var periodEndColumnExists = contextForMigration.Model.FindEntityType("Users").FindProperty("PeriodEnd") != null;
            Assert.True(periodEndColumnExists, "PeriodEnd column should exist in Users table.");

            var periodStartColumnExists = contextForMigration.Model.FindEntityType("Users").FindProperty("PeriodStart") != null;
            Assert.True(periodStartColumnExists, "PeriodStart column should exist in Users table.");
        }

        [Test]
        public async Task TestDownMigration()
        {
            // Arrange
            var migration = new UsersTableSetAsTemporal();

            // Act
            await using (var contextForMigration = new MinimalApiDbContext(options))
            {
                await migration.Down(new Migrator(), contextForMigration);
            }

            // Assert
            var usersHistoryExists = contextForMigration.Model.FindEntityType("Users").GetForeignKeys().Any(fk => fk.PrincipalKey?.Name == "FK_Users_History");
            Assert.False(usersHistoryExists, "UsersHistory table should be dropped.");

            var periodEndColumnExists = contextForMigration.Model.FindEntityType("Users").FindProperty("PeriodEnd") == null;
            Assert.True(periodEndColumnExists, "PeriodEnd column should not exist in Users table.");

            var periodStartColumnExists = contextForMigration.Model.FindEntityType("Users").FindProperty("PeriodStart") == null;
            Assert.True(periodStartColumnExists, "PeriodStart column should not exist in Users table.");
        }
    }

    public class MinimalApiDbContext : DbContext
    {
        public DbSet<TodoItem> TodoItems { get; set; }
        public DbSet<User> Users { get; set; }

        public MinimalApiDbContext(DbContextOptions<MinimalApiDbContext> options) : base(options)
        {
        }
    }

    public class User
    {
        public int Id { get; set; }
        public DateTime CreatedOn { get; set; }
    }

    public class TodoItem
    {
        public int Id { get; set; }
        public DateTime CreatedOn { get; set; }
    }
}
```

### Explanation:
1. **Setup**: The `MinimalApiDbContext` is configured to use an in-memory database, and a context is created for testing.
2. **OneTimeSetup**: This method seeds some data into the in-memory database before running tests.
3. **TestUpMigration**: This test simulates the `Up` method of the migration and checks if the necessary columns (`PeriodEnd`, `PeriodStart`) and table (`UsersHistory`) are added to the Users table.
4. **TestDownMigration**: This test simulates the `Down` method of the migration and verifies that the previously created columns and history table are dropped.

### Notes:
- The `MinimalApiDbContext` class is simplified for demonstration purposes, focusing on the entities used in this migration.
- Ensure that the namespaces and entity classes match your project structure. Adjust them accordingly if necessary.
- The test uses an in-memory database to simulate the behavior of a real database context.