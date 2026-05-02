_STACK_SIZE = DEFINED(_STACK_SIZE) ? _STACK_SIZE : 0x4000;
_HEAP_SIZE = DEFINED(_HEAP_SIZE) ? _HEAP_SIZE : 0x4000;
_EL0_STACK_SIZE = DEFINED(_EL0_STACK_SIZE) ? _EL0_STACK_SIZE : 0x1000;
_EL1_STACK_SIZE = DEFINED(_EL1_STACK_SIZE) ? _EL1_STACK_SIZE : 0x2000;
_EL2_STACK_SIZE = DEFINED(_EL2_STACK_SIZE) ? _EL2_STACK_SIZE : 0x1000;

MEMORY
{
   psu_ocm_ram_0_MEM_0 : ORIGIN = 0xFFFC0000, LENGTH = 0x00040000
}

ENTRY(_vector_table)

SECTIONS
{
.text : {
   KEEP(*(.vectors))
   *(.boot)
   *(.text)
   *(.text.*)
   *(.gnu.linkonce.t.*)
   *(.plt)
   *(.gnu_warning)
   *(.gcc_execpt_table)
   *(.glue_7)
   *(.glue_7t)
   *(.ARM.extab)
   *(.gnu.linkonce.armextab.*)
} > psu_ocm_ram_0_MEM_0

.note.gnu.build-id : {
   KEEP(*(.note.gnu.build-id))
} > psu_ocm_ram_0_MEM_0

.init (ALIGN(64)) : {
   KEEP(*(.init))
} > psu_ocm_ram_0_MEM_0

.fini (ALIGN(64)) : {
   KEEP(*(.fini))
} > psu_ocm_ram_0_MEM_0

.interp : {
   KEEP(*(.interp))
} > psu_ocm_ram_0_MEM_0

.note-ABI-tag : {
   KEEP(*(.note-ABI-tag))
} > psu_ocm_ram_0_MEM_0

.rodata (ALIGN(64)) : {
   __rodata_start = .;
   *(.rodata)
   *(.rodata.*)
   *(.gnu.linkonce.r.*)
   __rodata_end = .;
} > psu_ocm_ram_0_MEM_0

.rodata1 (ALIGN(64)) : {
   *(.rodata1)
   *(.rodata1.*)
} > psu_ocm_ram_0_MEM_0

.eh_frame : {
   *(.eh_frame)
} > psu_ocm_ram_0_MEM_0

.eh_framehdr : {
   *(.eh_framehdr)
} > psu_ocm_ram_0_MEM_0

.gcc_except_table : {
   *(.gcc_except_table)
} > psu_ocm_ram_0_MEM_0

.mmu_tbl0 (ALIGN(4096)) : {
   __mmu_tbl0_start = .;
   *(.mmu_tbl0)
   __mmu_tbl0_end = .;
} > psu_ocm_ram_0_MEM_0

.mmu_tbl1 (ALIGN(4096)) : {
   __mmu_tbl1_start = .;
   *(.mmu_tbl1)
   __mmu_tbl1_end = .;
} > psu_ocm_ram_0_MEM_0

.mmu_tbl2 (ALIGN(4096)) : {
   __mmu_tbl2_start = .;
   *(.mmu_tbl2)
   __mmu_tbl2_end = .;
} > psu_ocm_ram_0_MEM_0

.data (ALIGN(64)) : {
   __data_start = .;
   *(.data)
   *(.data.*)
   *(.gnu.linkonce.d.*)
   *(.jcr)
   *(.got)
   *(.got.plt)
   __data_end = .;
} > psu_ocm_ram_0_MEM_0

.data1 (ALIGN(64)) : {
   *(.data1)
   *(.data1.*)
} > psu_ocm_ram_0_MEM_0

.tdata (ALIGN(64)) : {
   *(.tdata)
   *(.tdata.*)
   *(.gnu.linkonce.td.*)
} > psu_ocm_ram_0_MEM_0

.got : {
   *(.got)
} > psu_ocm_ram_0_MEM_0

.got1 : {
   *(.got1)
} > psu_ocm_ram_0_MEM_0

.got2 : {
   *(.got2)
} > psu_ocm_ram_0_MEM_0

.fixup : {
   *(.fixup)
} > psu_ocm_ram_0_MEM_0

.ARM.exidx : {
   __exidx_start = .;
   *(.ARM.exidx*)
   *(.gnu.linkonce.armexidix.*.*)
   __exidx_end = .;
} > psu_ocm_ram_0_MEM_0

.preinit_array (ALIGN(64)) : {
   __preinit_array_start = .;
   KEEP(*(SORT(.preinit_array.*)))
   KEEP(*(.preinit_array))
   __preinit_array_end = .;
} > psu_ocm_ram_0_MEM_0

.init_array (ALIGN(64)) : {
   __init_array_start = .;
   KEEP(*(SORT(.init_array.*)))
   KEEP(*(.init_array))
   __init_array_end = .;
} > psu_ocm_ram_0_MEM_0

.fini_array (ALIGN(64)) : {
   __fini_array_start = .;
   KEEP(*(SORT(.fini_array.*)))
   KEEP(*(.fini_array))
   __fini_array_end = .;
} > psu_ocm_ram_0_MEM_0

.sdata (ALIGN(64)) : {
   __sdata_start = .;
   *(.sdata)
   *(.sdata.*)
   *(.gnu.linkonce.s.*)
   __sdata_end = .;
} > psu_ocm_ram_0_MEM_0

.sdata2 (ALIGN(64)) : {
   *(.sdata2)
   *(.sdata2.*)
   *(.gnu.linkonce.s2.*)
} > psu_ocm_ram_0_MEM_0

.sbss (NOLOAD) : {
   . = ALIGN(64);
   __sbss_start = .;
   *(.sbss)
   *(.sbss.*)
   *(.gnu.linkonce.sb.*)
   . = ALIGN(64);
   __sbss_end = .;
} > psu_ocm_ram_0_MEM_0

.sbss2 (ALIGN(64)) : {
   *(.sbss2)
   *(.sbss2.*)
   *(.gnu.linkonce.sb2.*)
} > psu_ocm_ram_0_MEM_0

.tbss (ALIGN(64)) : {
   *(.tbss)
   *(.tbss.*)
   *(.gnu.linkonce.tb.*)
} > psu_ocm_ram_0_MEM_0

.bss (NOLOAD) : {
   . = ALIGN(64);
   __bss_start__ = .;
   *(.bss)
   *(.bss.*)
   *(.gnu.linkonce.b.*)
   *(COMMON)
   . = ALIGN(64);
   __bss_end__ = .;
} > psu_ocm_ram_0_MEM_0

_SDA_BASE_ = __sdata_start + ((__sbss_end - __sdata_start) / 2);

.heap (NOLOAD) : {
   . = ALIGN(16);
   _heap = .;
   HeapBase = .;
   _heap_start = .;
   . += _HEAP_SIZE;
   _heap_end = .;
   HeapLimit = .;
} > psu_ocm_ram_0_MEM_0

.stack (NOLOAD) : {
   . = ALIGN(16);
   _el3_stack_end = .;
   . += _STACK_SIZE;
   __el3_stack = .;
   . += _STACK_SIZE;
   . = ALIGN(16);
   __el2_stack = .;
   . += _EL2_STACK_SIZE;
   . = ALIGN(16);
   __el1_stack = .;
   . += _EL1_STACK_SIZE;
   . = ALIGN(16);
   __el0_stack = .;
   . += _EL0_STACK_SIZE;
   . = ALIGN(16);
   __stack = .;
   _stack = .;
   _stack_end = .;
   _end = .;
} > psu_ocm_ram_0_MEM_0

.ARM.attributes : {
   KEEP(*(.ARM.attributes))
} > psu_ocm_ram_0_MEM_0
}
