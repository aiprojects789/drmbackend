const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  // Deploy ArtworkRegistry
  const ArtworkRegistry = await ethers.getContractFactory("ArtworkRegistry");
  const registry = await ArtworkRegistry.deploy();
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();

  // Deploy ArtworkLicensing
  const ArtworkLicensing = await ethers.getContractFactory("ArtworkLicensing");
  const licensing = await ArtworkLicensing.deploy(registryAddress);
  await licensing.waitForDeployment();
  const licensingAddress = await licensing.getAddress();

  // Configure licensing contract in registry
  await registry.setLicensingContract(licensingAddress);

  // Prepare addresses for saving
  const networkName = network.name === "hardhat" ? "localhost" : network.name;
  const contracts = {
    [networkName]: {
      registry: registryAddress,
      licensing: licensingAddress
    },
    network: networkName
  };

  // Merge with existing addresses if file exists
  let allAddresses = {};
  if (fs.existsSync('contract-addresses.json')) {
    allAddresses = JSON.parse(fs.readFileSync('contract-addresses.json'));
  }
  
  // Update with new deployments
  allAddresses[networkName] = contracts[networkName];
  allAddresses.network = networkName;

  fs.writeFileSync('contract-addresses.json', JSON.stringify(allAddresses, null, 2));
  console.log("Contract addresses saved to contract-addresses.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });