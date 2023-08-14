from prometheus_client import Counter, Histogram, Summary, Gauge
import grpc
import asyncio
from timeit import default_timer
from interceptor import utils

from grpc.aio import ServerInterceptor
from interceptor import grpc_utils
class ServerMetricsInterceptor(ServerInterceptor):
    def __init__(self):
        self.request_counter = Counter(
            'grpc_server_requests_total', 'Total server requests', ['grpc_service', 'grpc_method']
        )
        self.response_counter = Counter(
            'grpc_server_responses_total', 'Total server responses', ['grpc_service', 'grpc_method', 'grpc_status']
        )
        self.request_latency = Histogram(
            'grpc_server_request_latency_seconds', 'Request latency', ['grpc_service', 'grpc_method']
        )
        self.request_size = Summary(
            'grpc_server_request_size_bytes', 'Request size in bytes', ['grpc_service', 'grpc_method']
            )
        self.response_size = Summary(
            'grpc_server_response_size_bytes', 'Response size in bytes', ['grpc_service', 'grpc_method']
        )
        self.active_requests = Gauge(
            'grpc_server_active_requests', 'Number of active requests', ['grpc_service', 'grpc_method']
        )


    async def intercept_service(self, continuation, handler_call_details):
        print("INTERCEPTED")
        service_name, method_name = handler_call_details.method.split('/')[-2:]
        self.request_counter.labels(service_name, method_name).inc()

        start = default_timer()
        # Measure request size
        request_size = utils.get_size(handler_call_details.invocation_metadata)
        self.request_size.labels(service_name, method_name).observe(request_size)

        self.active_requests.labels(service_name, method_name).inc()

        code = grpc.StatusCode.UNKNOWN

        try:
            response = await continuation(handler_call_details)
            code = grpc.StatusCode.OK
        except grpc.aio.AioRpcError as e:
            code = e.code()
            raise  # Re-raise the exception after recording the status code

        finally:
            print("Finished handling request, start time = ", start, ", current = " , default_timer(), " = ", max(default_timer() - start, 0))
            self.request_latency.labels(service_name, method_name).observe(max(default_timer() - start, 0))
            response_size = utils.get_size(response) if code == grpc.StatusCode.OK else 0
            self.response_size.labels(service_name, method_name).observe(response_size)
            self.response_counter.labels(service_name, method_name, str(code)).inc()
            self.active_requests.labels(service_name, method_name).dec()
            print("INTERCEPTED END")
        return response
