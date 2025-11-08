// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract AlertStorage {
    struct Alert {
        uint id;
        string userId;
        string description;
        string riskLevel;
        uint timestamp;
    }

    Alert[] public alerts;
    event AlertRecorded(uint id, string userId, string description, string riskLevel, uint timestamp);

    function recordAlert(string memory _userId, string memory _description, string memory _riskLevel) public {
        uint alertId = alerts.length + 1;
        alerts.push(Alert(alertId, _userId, _description, _riskLevel, block.timestamp));
        emit AlertRecorded(alertId, _userId, _description, _riskLevel, block.timestamp);
    }

    function getAllAlerts() public view returns (Alert[] memory) {
        return alerts;
    }
}
