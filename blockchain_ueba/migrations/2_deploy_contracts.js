const AlertStorage = artifacts.require("AlertStorage");

module.exports = function (deployer) {
  deployer.deploy(AlertStorage);
};
