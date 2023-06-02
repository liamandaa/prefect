"""
Utilities for inspection of stack frames and threads.
"""

from types import FrameType
import linecache
import sys
import threading
import time
import dis
from typing import List
import functools
import traceback


@functools.cache
def trace_on() -> bool:
    # We cache this to avoid overhead but to also delay checking the value until the
    # first debug statement is printed. This is not typically how we handle settings
    # but for low-level debug prints we shall.

    from prefect.settings import PREFECT_DEBUG_MODE, PREFECT_TEST_MODE

    return PREFECT_DEBUG_MODE.value() or PREFECT_TEST_MODE.value()


def trace(message, *args, exc_info: bool = False, **kwargs) -> None:
    """
    Print a trace debugging message.
    """
    if trace_on():
        prefix = f"{round(time.monotonic(), 3)} | {threading.current_thread().name} | "
        message = message % args
        message = message % kwargs
        print(prefix + message, file=sys.stderr, flush=True)

        if exc_info:
            traceback.print_exc(file=sys.stderr)


"""
The following functions are dervived from dask/distributed which is licensed under the 
BSD 3-Clause License.

Copyright (c) 2015, Anaconda, Inc. and contributors
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


def _f_lineno(frame: FrameType) -> int:
    """Work around some frames lacking an f_lineno
    See: https://bugs.python.org/issue47085
    """
    f_lineno = frame.f_lineno
    if f_lineno is not None:
        return f_lineno

    f_lasti = frame.f_lasti
    code = frame.f_code
    prev_line = code.co_firstlineno

    for start, next_line in dis.findlinestarts(code):
        if f_lasti < start:
            return prev_line
        prev_line = next_line

    return prev_line


def repr_frame(frame: FrameType) -> str:
    """Render a frame as a line for inclusion into a text traceback"""
    co = frame.f_code
    f_lineno = _f_lineno(frame)
    text = f'  File "{co.co_filename}", line {f_lineno}, in {co.co_name}'
    line = linecache.getline(co.co_filename, f_lineno, frame.f_globals).lstrip()
    return text + "\n\t" + line


def call_stack(frame: FrameType) -> List[str]:
    """Create a call text stack from a frame"""
    L = []
    cur_frame: FrameType | None = frame
    while cur_frame:
        L.append(repr_frame(cur_frame))
        cur_frame = cur_frame.f_back
    return L[::-1]


def stack_for_threads(*threads: threading.Thread) -> List[str]:
    frames = sys._current_frames()
    try:
        lines = []
        for thread in threads:
            lines.append(
                f"------ Call stack of {thread.name} ({hex(thread.ident)}) -----"
            )
            thread_frames = frames.get(thread.ident)
            if thread_frames:
                lines.append("".join(call_stack(thread_frames)))
            else:
                lines.append("No stack frames found")
    finally:
        del frames

    return lines