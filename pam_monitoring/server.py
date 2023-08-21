from prometheus_client import Counter, Histogram, Summary, Gauge
from grpc_interceptor.exceptions import GrpcException
from grpc_interceptor.server import AsyncServerInterceptor
from typing import Callable, Any

import grpc
import asyncio
from timeit import default_timer
from pam_monitoring import utils

from grpc.aio import ServerInterceptor

class AsyncExceptionToStatusInterceptor(AsyncServerInterceptor):

#class ServerMetricsInterceptor(ServerInterceptor):
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

    async def intercept(
        self,
        method: Callable,
        request_or_iterator: Any,
        context: grpc.ServicerContext,
        method_name: str,
    ) -> Any:
        try:
            start = default_timer()
            service_name, service_method = method_name.split('/')[-2:]
            self.request_counter.labels(service_name, service_method).inc()

            request_size = utils.get_size(request_or_iterator)

            self.request_size.labels(service_name, service_method).observe(request_size)
            self.active_requests.labels(service_name, service_method).inc()

            response_or_iterator = method(request_or_iterator, context)
            if not hasattr(response_or_iterator, "__aiter__"):
                # Unary, just await and return the response
                return await response_or_iterator
        except GrpcException as e:
            await context.set_code(e.status_code)
            await context.set_details(e.details)

            raise
        finally:
            self.request_latency.labels(service_name, service_method).observe(max(default_timer() - start, 0))
            response_size = utils.get_size(response_or_iterator) if utils.GetStatusFromCode(context.code()) == grpc.StatusCode.OK else 0
            self.response_size.labels(service_name, service_method).observe(response_size)
            self.response_counter.labels(service_name, service_method, str(utils.GetStatusFromCode(context.code()))).inc()
            self.active_requests.labels(service_name, service_method).dec()
        # Server streaming responses, delegate to an async generator helper.
        # Note that we do NOT await this.
        # but we re-add 1 to the acive requests as the previous one was decreased in the finally block.
        # This is kind of a hack, but seems to be the simplest way to fix it without having do go on a full-on refactor.
        self.active_requests.labels(service_name, service_method).inc()
        return self._intercept_streaming(response_or_iterator, context, service_name, service_method, start)


    async def _intercept_streaming(self, iterator, context, service_name, service_method, start):

        response_size = 0
        try:
            async for r in iterator:
                yield r
                response_size += utils.get_size(r)

        except GrpcException as e:
            await context.set_code(e.status_code)
            await context.set_details(e.details)
            raise
        finally:
            self.request_latency.labels(service_name, service_method).observe(max(default_timer() - start, 0))
            self.response_size.labels(service_name, service_method).observe(response_size)
            self.response_counter.labels(service_name, service_method, utils.GetStatusFromCode(context.code())).inc()
            self.active_requests.labels(service_name, service_method).dec()
