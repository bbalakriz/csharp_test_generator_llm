Certainly! Below is a complete NUnit test class for the `TodoItemOutput` class. The test class is named `TodoItemOutputTests`, and it is placed within the `GeneratedTests` namespace. I have included test methods that cover various scenarios to ensure the `TodoItemOutput` class works as expected.

```csharp
using MinimalApi.ViewModels;
using NUnit.Framework;

namespace GeneratedTests
{
    [TestFixture]
    public class TodoItemOutputTests
    {
        [Test]
        public void TestTodoItemOutput_CorrectParametersAreSet()
        {
            // Arrange
            string title = "Buy groceries";
            bool isCompleted = false;
            DateTime createdOn = new DateTime(2023, 10, 5);

            // Act
            TodoItemOutput item = new TodoItemOutput(title, isCompleted, createdOn);

            // Assert
            Assert.AreEqual(title, item.Title);
            Assert.AreEqual(isCompleted, item.IsCompleted);
            Assert.AreEqual(createdOn, item.CreatedOn);
        }

        [Test]
        public void TestTodoItemOutput_NullTitle()
        {
            // Arrange
            string title = null;
            bool isCompleted = true;
            DateTime createdOn = new DateTime(2023, 10, 6);

            // Act
            TodoItemOutput item = new TodoItemOutput(title, isCompleted, createdOn);

            // Assert
            Assert.IsNull(item.Title);
            Assert.AreEqual(isCompleted, item.IsCompleted);
            Assert.AreEqual(createdOn, item.CreatedOn);
        }

        [Test]
        public void TestTodoItemOutput_EmptyStringTitle()
        {
            // Arrange
            string title = "";
            bool isCompleted = false;
            DateTime createdOn = new DateTime(2023, 10, 7);

            // Act
            TodoItemOutput item = new TodoItemOutput(title, isCompleted, createdOn);

            // Assert
            Assert.AreEqual(title, item.Title);
            Assert.AreEqual(isCompleted, item.IsCompleted);
            Assert.AreEqual(createdOn, item.CreatedOn);
        }

        [Test]
        public void TestTodoItemOutput_CompletedItem()
        {
            // Arrange
            string title = "Submit report";
            bool isCompleted = true;
            DateTime createdOn = new DateTime(2023, 10, 8);

            // Act
            TodoItemOutput item = new TodoItemOutput(title, isCompleted, createdOn);

            // Assert
            Assert.AreEqual(title, item.Title);
            Assert.IsTrue(item.IsCompleted);
            Assert.AreEqual(createdOn, item.CreatedOn);
        }

        [Test]
        public void TestTodoItemOutput_UncompletedItem()
        {
            // Arrange
            string title = "Attend meeting";
            bool isCompleted = false;
            DateTime createdOn = new DateTime(2023, 10, 9);

            // Act
            TodoItemOutput item = new TodoItemOutput(title, isCompleted, createdOn);

            // Assert
            Assert.AreEqual(title, item.Title);
            Assert.IsFalse(item.IsCompleted);
            Assert.AreEqual(createdOn, item.CreatedOn);
        }
    }
}
```

### Explanation:
- **TestTodoItemOutput_CorrectParametersAreSet**: Tests the basic scenario where all parameters are provided correctly.
- **TestTodoItemOutput_NullTitle**: Tests that when `title` is null, it is handled appropriately by setting `Title` to `null`.
- **TestTodoItemOutput_EmptyStringTitle**: Tests that an empty string for `title` does not cause issues.
- **TestTodoItemOutput_CompletedItem**: Tests a scenario where the `isCompleted` property is set to true.
- **TestTodoItemOutput_UncompletedItem**: Tests a scenario where the `isCompleted` property is set to false.

This test class covers a variety of scenarios to ensure that the `TodoItemOutput` class behaves as expected.