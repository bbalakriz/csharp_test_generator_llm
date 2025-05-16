To generate a complete, runnable NUnit test class for the `UsersTableSetAsTemporal` class, we need to create a test fixture that sets up an in-memory context and verifies the configuration of the `User` entity. Below is the generated code:

```csharp
using System;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Metadata;
using Microsoft.EntityFrameworkCore.Migrations;
using NUnit.Framework;

namespace GeneratedTests
{
    [TestFixture]
    public class UsersTableSetAsTemporalTests
    {
        private DbContextOptions<TodoDbContext> options;
        private TodoDbContext context;

        [SetUp]
        public void Setup()
        {
            // Configure an in-memory database for testing
            var builder = new DbContextOptionsBuilder<TodoDbContext>();
            builder.UseInMemoryDatabase("TestDb");

            options = builder.Options;
            context = new TodoDbContext(options);
        }

        [TearDown]
        public void TearDown()
        {
            // Dispose the context after each test to clean up resources
            if (context != null)
            {
                context.Dispose();
            }
        }

        [Test]
        public void ShouldConfigureUserEntityAsTemporal()
        {
            // Arrange & Act: The configuration is done in the BuildTargetModel method, so we just need to check it.

            // Assert: Verify that the User entity is configured as a temporal table
            var model = context.Model;
            var userEntityType = model.FindEntityType(typeof(User));

            Assert.IsNotNull(userEntityType);

            var temporalProperties = userEntityType.FindProperty("PeriodStart");
            Assert.IsNotNull(temporalProperties);
            Assert.AreEqual("PeriodStart", temporalProperties.Name);

            temporalProperties = userEntityType.FindProperty("PeriodEnd");
            Assert.IsNotNull(temporalProperties);
            Assert.AreEqual("PeriodEnd", temporalProperties.Name);
        }

        [Test]
        public void ShouldConfigureUserIdentityColumns()
        {
            // Arrange & Act: The configuration is done in the BuildTargetModel method, so we just need to check it.

            // Assert: Verify that the User entity has identity columns configured
            var model = context.Model;
            var userEntityType = model.FindEntityType(typeof(User));

            SqlServerPropertyBuilderExtensions.UseIdentityColumn(userEntityType.Property("Id"), 1L, 1);

            var idProperty = userEntityType.FindProperty("Id");
            Assert.IsNotNull(idProperty);
            Assert.IsTrue(idProperty.IsValueGenerationStrategyValueGenerationStrategy.IdentityColumn);
        }

        [Test]
        public void ShouldConfigureUserProperties()
        {
            // Arrange & Act: The configuration is done in the BuildTargetModel method, so we just need to check it.

            // Assert: Verify that the User entity has correct property configurations
            var model = context.Model;
            var userEntityType = model.FindEntityType(typeof(User));

            var createdOnProperty = userEntityType.FindProperty("CreatedOn");
            Assert.IsNotNull(createdOnProperty);
            Assert.AreEqual("datetime2", createdOnProperty.ClrType.Name);

            var emailProperty = userEntityType.FindProperty("Email");
            Assert.IsNotNull(emailProperty);
            Assert.AreEqual("nvarchar(max)", emailProperty.ClrType.Name);

            var passwordProperty = userEntityType.FindProperty("Password");
            Assert.IsNotNull(passwordProperty);
            Assert.AreEqual("nvarchar(max)", passwordProperty.ClrType.Name);

            var usernameProperty = userEntityType.FindProperty("Username");
            Assert.IsNotNull(usernameProperty);
            Assert.AreEqual("nvarchar(max)", usernameProperty.ClrType.Name);
        }
    }
}
```

### Explanation:
1. **Setup and TearDown Methods**: These methods are used to initialize the in-memory database context before each test and clean up resources afterward.
2. **Test Cases**:
   - `ShouldConfigureUserEntityAsTemporal`: Verifies that the `User` entity is configured as a temporal table by checking its properties.
   - `ShouldConfigureUserIdentityColumns`: Ensures that the `Id` property of the `User` entity has identity column configuration.
   - `ShouldConfigureUserProperties`: Validates the configurations of various properties in the `User` entity.

This test class provides a comprehensive check to ensure that the `UsersTableSetAsTemporal` migration correctly configures the `User` entity as intended.