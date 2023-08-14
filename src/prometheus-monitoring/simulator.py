from concurrent import futures
import grpc

import asyncio
import my_service_pb2
import my_service_pb2_grpc
import time
import random, string # for random string generation

from prometheus_client import Counter, Histogram, start_http_server

import interceptor.server
import interceptor.client

class MyServiceServicer(my_service_pb2_grpc.MyServiceServicer):

    async def UnaryCall(self, request, context):
        print("FUNCTION START")
        # Randomly sleep between 1-3 seconds
        await asyncio.sleep(random.randint(100, 3000) / 1000)

        # Randomly generate an error
        if random.random() < 0.00: # 3% chance of this to happen
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('A test error')
            return my_service_pb2.Response()

        print("FUNCTION END")        
        return my_service_pb2.Response(message='Hello, %s!' % request.message)

    def ServerStreamingCall(self, request, context):
        # Randomly sleep between 1-2 seconds
        time.sleep(random.randint(1000, 3000) / 1000)

        # Randomly generate an error
        if random.random() < 0.13: # 13% chance of this to happen
            context.set_code(random.randint(2,5))
            context.set_details('A test error')
            return my_service_pb2.Response()
        
        for i in range(5):
            yield my_service_pb2.Response(message='Server Streaming Response {}'.format(i))

    def ClientStreamingCall(self, request_iterator, context):
        # Randomly sleep between 1-2 seconds
        time.sleep(random.randint(1000, 3000) / 1000)

                # Randomly generate an error
        if random.random() < 0.13: # 13% chance of this to happen
            context.set_code(random.randint(2,5))
            context.set_details('A test error')
            return my_service_pb2.Response()
        
        for request in request_iterator:
            print(request.message)
        return my_service_pb2.Response(message='Client Streaming Response')

    def BidirectionalStreamingCall(self, request_iterator, context):
        # Randomly sleep between 1-2 seconds
        time.sleep(random.randint(1000, 3000) / 1000)

                # Randomly generate an error
        if random.random() < 0.13: # 13% chance of this to happen
            context.set_code(random.randint(2,5))
            context.set_details('A test error')
            return my_service_pb2.Response()
        

        for request in request_iterator:
            yield my_service_pb2.Response(message='Bidirectional Streaming Response {}'.format(request.message))

async def serve():
    server = grpc.aio.server(interceptors=[interceptor.server.ServerMetricsInterceptor()])
    my_service_pb2_grpc.add_MyServiceServicer_to_server(MyServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    await server.wait_for_termination()



def _getClientStub():
        channel =  grpc.aio.insecure_channel('localhost:50051', interceptors=[interceptor.client.ClientMetricsInterceptor()])
        stub = my_service_pb2_grpc.MyServiceStub(channel)
        return stub

def randomString(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

async def run():
        client = _getClientStub()
        while(True):
                start = time.time()
                response = await client.UnaryCall(my_service_pb2.Request(message=randomString(12)))
                print("UnaryCall took ", (time.time() - start), "seconds")


                await asyncio.sleep(5)


"""
            # Server streaming RPC
            try:
                response_iterator = client.ServerStreamingCall(my_service_pb2.Request(message='Server Streaming Call'))
                async for response in response_iterator:
                    print(response.message)
                print("ServerStreaming took ", (time.time() - start), "seconds")
            except grpc.aio.AioRpcError:
                pass

            # Client streaming RPC
            try:
                requests = (my_service_pb2.Request(message='Client Streaming Call {}'.format(i)) for i in range(5))
                response = await client.ClientStreamingCall(requests)
                print(response.message)

                print("ClientStreaming took ", (time.time() - start), "seconds")
            except grpc.aio.AioRpcError:
                pass

            # Bidirectional streaming RPC
            try:
                requests = (my_service_pb2.Request(message='Bidirectional Streaming Call {}'.format(i)) for i in range(5))
                response_iterator = client.BidirectionalStreamingCall(requests)
                async for response in response_iterator:
                    print(response.message)

                print("Bidirectional took ", (time.time() - start), "seconds")

            except grpc.aio.AioRpcError:
                pass
"""




async def main():
    await asyncio.gather(
        serve(),
        run(),
)
    
if __name__ == '__main__':
    start_http_server(8000)
    asyncio.run(main())