const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  
  console.log("Deploying contracts with the account:", deployer.address);
  console.log("Account balance:", (await hre.ethers.provider.getBalance(deployer.address)).toString());

  // 1. Deploy ERC20 Token
  const MyToken = await hre.ethers.getContractFactory("MyToken");
  const token = await MyToken.deploy(hre.ethers.parseEther("1000000")); // 1M tokens
  await token.waitForDeployment();
  console.log("MyToken deployed to:", await token.getAddress());

  // 2. Deploy PaymentSplitter
  const payees = [
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", // Account 1
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"  // Account 2
  ];
  const shares = [60, 40]; // 60% to Account 1, 40% to Account 2
  
  const PaymentSplitter = await hre.ethers.getContractFactory("PaymentSplitter");
  const splitter = await PaymentSplitter.deploy(payees, shares);
  await splitter.waitForDeployment();
  console.log("PaymentSplitter deployed to:", await splitter.getAddress());

  // 3. Deploy TimeLock
  const beneficiary = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8";
  const releaseTime = Math.floor(Date.now() / 1000) + 86400; // 24 hours from now
  
  const TimeLock = await hre.ethers.getContractFactory("TimeLock");
  const timelock = await TimeLock.deploy(beneficiary, releaseTime);
  await timelock.waitForDeployment();
  console.log("TimeLock deployed to:", await timelock.getAddress());

  // Save contract addresses
  const contracts = {
    token: await token.getAddress(),
    splitter: await splitter.getAddress(),
    timelock: await timelock.getAddress(),
    network: hre.network.name
  };
  
  const fs = require("fs");
  fs.writeFileSync("contract-addresses.json", JSON.stringify(contracts, null, 2));
  console.log("Contract addresses saved to contract-addresses.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });