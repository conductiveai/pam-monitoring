import grpc
import asyncio
import my_service_pb2
import my_service_pb2_grpc
import asddd.a
async def run():
        channel =  grpc.aio.insecure_channel('localhost:50051')
        stub = my_service_pb2_grpc.MyServiceStub(channel)
        response = await stub.SayBye(my_service_pb2.HelloRequest(name='you'))
        print("Server responded with: " + response.message)
        asddd.a.B()


async def main():
    await asyncio.gather(
        run()
)
    
if __name__ == '__main__':
    asyncio.run(main())
