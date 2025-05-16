Sure! Below is a complete NUnit test class that meets your requirements. The `PagedResults` class does not have any methods to test directly since it's just a simple model class. However, we can still create tests for its properties and constructors.

Here’s the complete NUnit test class:

```csharp
using System.Collections.Generic;
using NUnit.Framework;

namespace GeneratedTests
{
    [TestFixture]
    public class PagedResultsTests
    {
        private PagedResults<int> _pagedResults;

        [SetUp]
        public void Setup()
        {
            // Setup a default instance of PagedResults for testing
            _pagedResults = new PagedResults<int>
            {
                PageNumber = 1,
                PageSize = 25,
                TotalNumberOfPages = 4,
                TotalNumberOfRecords = 100,
                Results = new List<int> { 1, 2, 3 }
            };
        }

        [Test]
        public void PagedResults_CanBeIntializedWithValidProperties()
        {
            // Arrange
            var pageNumber = 1;
            var pageSize = 25;
            var totalNumberOfPages = 4;
            var totalNumberOfRecords = 100;
            var results = new List<int> { 1, 2, 3 };

            // Act & Assert
            _pagedResults.PageNumber.Should().Be(pageNumber);
            _pagedResults.PageSize.Should().Be(pageSize);
            _pagedResults.TotalNumberOfPages.Should().Be(totalNumberOfPages);
            _pagedResults.TotalNumberOfRecords.Should().Be(totalNumberOfRecords);
            _pagedResults.Results.Should().BeEquivalentTo(results);
        }

        [Test]
        public void PagedResults_PageNumber_ShouldDefaultTo1()
        {
            // Arrange
            var pagedResults = new PagedResults<int>();

            // Act & Assert
            pagedResults.PageNumber.Should().Be(1);
        }

        [Test]
        public void PagedResults_Properties_CanBeNull()
        {
            // Arrange
            _pagedResults.Results = null;

            // Act & Assert
            _pagedResults.Results.Should().BeNull();
        }

        [Test]
        public void PagedResults_TotalNumberOfPages_CannotBeNegativeOrZero()
        {
            // Arrange & Act & Assert
            Assert.Throws<ArgumentException>(() => new PagedResults<int> { TotalNumberOfPages = 0 });
            Assert.Throws<ArgumentException>(() => new PagedResults<int> { TotalNumberOfPages = -1 });

            _pagedResults.TotalNumberOfPages.Should().BeGreaterThan(0);
        }

        [Test]
        public void PagedResults_TotalNumberOfRecords_CannotBeNegativeOrZero()
        {
            // Arrange & Act & Assert
            Assert.Throws<ArgumentException>(() => new PagedResults<int> { TotalNumberOfRecords = 0 });
            Assert.Throws<ArgumentException>(() => new PagedResults<int> { TotalNumberOfRecords = -1 });

            _pagedResults.TotalNumberOfRecords.Should().BeGreaterThan(0);
        }

        [Test]
        public void PagedResults_PageSize_CannotBeNegativeOrZero()
        {
            // Arrange & Act & Assert
            Assert.Throws<ArgumentException>(() => new PagedResults<int> { PageSize = 0 });
            Assert.Throws<ArgumentException>(() => new PagedResults<int> { PageSize = -1 });

            _pagedResults.PageSize.Should().BeGreaterThan(0);
        }
    }
}
```

### Explanation:
- **Setup Method**: Initializes an instance of `PagedResults<int>` with some default values.
- **TestFixture**: Marks the class as a test fixture, which means NUnit will create and destroy instances for each test method.
- **Test Methods**:
  - **CanBeIntializedWithValidProperties**: Tests if the properties can be initialized with valid values.
  - **PageNumber_ShouldDefaultTo1**: Verifies that `PageNumber` defaults to 1 when not specified.
  - **Properties_CanBeNull**: Ensures that `Results` can be set to null.
  - **TotalNumberOfPages_CannotBeNegativeOrZero**: Checks for invalid values in `TotalNumberOfPages`.
  - **TotalNumberOfRecords_CannotBeNegativeOrZero**: Validates the `TotalNumberOfRecords` property.
  - **PageSize_CannotBeNegativeOrZero**: Ensures that `PageSize` cannot be zero or negative.

### Dependencies:
Ensure you have NUnit and FluentAssertions installed via NuGet. You can install them by running:

```shell
dotnet add package NUnit
dotnet add package FluentAssertions
```

This setup should provide a good foundation for testing the `PagedResults` class in your application.