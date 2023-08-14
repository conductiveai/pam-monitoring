from concurrent import futures
import grpc
import asyncio
import my_service_pb2
import my_service_pb2_grpc

class MyServiceServicer(my_service_pb2_grpc.MyServiceServicer):

    async def SayHello(self, request, context):
        return my_service_pb2.HelloResponse(message='Hello, %s!' % request.name)

    async def SayBye(self, request, context):
        return my_service_pb2.HelloResponse(message='Hello, %s!' % request.name)

async def serve():
    server = grpc.aio.server()
    my_service_pb2_grpc.add_MyServiceServicer_to_server(MyServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()

async def main():
    await asyncio.gather(
        serve()
)
    
if __name__ == '__main__':
    asyncio.run(main())

