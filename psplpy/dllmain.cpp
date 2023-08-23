﻿// dllmain.cpp : Define the entry point for the DLL application.
#include "pch.h"

BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
                     )
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}

extern "C" __declspec(dllexport) int add(int a, int b);
extern "C" __declspec(dllexport) int all(int a);

int add(int a, int b) {
    return a + b;
}

int natural_number_sum(int a) {
    int sum = 0;
    for (int i = 0; i < a; i++) {
        sum += i;
    }
    return sum;
}
