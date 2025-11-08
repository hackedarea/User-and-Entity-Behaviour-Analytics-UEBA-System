const Alert = artifacts.require("Alert");

/*
 * uncomment accounts to access the test accounts made available by the
 * Ethereum client
 * See docs: https://www.trufflesuite.com/docs/truffle/testing/writing-tests-in-javascript
 */
contract("Alert", function (/* accounts */) {
  it("should assert true", async function () {
    await Alert.deployed();
    return assert.isTrue(true);
  });
});
