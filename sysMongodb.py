import asyncio
import motor.motor_asyncio

# Connect to MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
db = client['mydatabase']
collection = db['mycollection']

async def main():
    # Insert a document
    document = {'name': 'John Doe', 'age': 30}
    await collection.insert_one(document)

    # Find documents
    async for result in collection.find({'age': {'$gt': 25}}):
        print(result)

    # Close the connection
    await client.close()
    # TODO: #12 TypeError: object NoneType can't be used in 'await' expression

# Run the event loop
asyncio.run(main())
