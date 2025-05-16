Sure! Below is a complete NUnit test class for the `UserInput` class. The test class includes namespaces, using directives, and several test methods to cover different scenarios involving `Username` and `Password`.

```csharp
using MinimalApi.ViewModels;
using NUnit.Framework;

namespace GeneratedTests
{
    [TestFixture]
    public class UserInputTests
    {
        private UserInput _userInput;

        // Setup method to initialize the user input object before each test
        [SetUp]
        public void Setup()
        {
            _userInput = new UserInput();
        }

        // Test case for when both Username and Password are null
        [Test]
        public void GivenBothPropertiesAreNull_ThenUsernameAndPasswordShouldBeNull()
        {
            Assert.IsNull(_userInput.Username);
            Assert.IsNull(_userInput.Password);
        }

        // Test case for when only Username is set
        [Test]
        public void GivenOnlyUsernameIsSet_ThenUsernameShouldNotBeNullAndPasswordShouldBeNull()
        {
            _userInput.Username = "testUser";
            Assert.IsNotNull(_userInput.Username);
            Assert.IsNull(_userInput.Password);
        }

        // Test case for when only Password is set
        [Test]
        public void GivenOnlyPasswordIsSet_ThenUsernameShouldBeNullAndPasswordShouldNotBeNull()
        {
            _userInput.Password = "securePass123";
            Assert.IsNull(_userInput.Username);
            Assert.IsNotNull(_userInput.Password);
        }

        // Test case for when both Username and Password are set
        [Test]
        public void GivenBothPropertiesAreSet_ThenUsernameAndPasswordShouldNotBeNull()
        {
            _userInput.Username = "testUser";
            _userInput.Password = "securePass123";
            Assert.IsNotNull(_userInput.Username);
            Assert.IsNotNull(_userInput.Password);
        }
    }
}
```

### Explanation:
- **Namespaces and Using Directives**: The `MinimalApi.ViewModels` namespace is used for the class being tested, while `NUnit.Framework` is used for NUnit attributes.
- **TestFixture Attribute**: Marks the class as a test fixture.
- **Setup Method**: Initializes an instance of `UserInput` before each test method runs.
- **Test Methods**:
  - `GivenBothPropertiesAreNull_ThenUsernameAndPasswordShouldBeNull`: Tests that both properties are initially null.
  - `GivenOnlyUsernameIsSet_ThenUsernameShouldNotBeNullAndPasswordShouldBeNull`: Sets only the username and checks if it's not null while the password is still null.
  - `GivenOnlyPasswordIsSet_ThenUsernameShouldBeNullAndPasswordShouldNotBeNull`: Sets only the password and checks if the username is null while the password is not null.
  - `GivenBothPropertiesAreSet_ThenUsernameAndPasswordShouldNotBeNull`: Sets both properties and checks if they are not null.

This test class ensures that all possible combinations of setting or leaving the `Username` and `Password` properties are covered.