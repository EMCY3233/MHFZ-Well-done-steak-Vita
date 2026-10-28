"""Compile own sources for ARM stack metadata; no client or executable run."""
from pathlib import Path
import subprocess,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sdk=ROOT/'analysis-tools/vitasdk-win-20260825/bin';build=HERE/'memory-probe';build.mkdir(exist_ok=True)
names=['private_store','batch_commit','batch_plan','snapshot_reader','manifest_reader','record_ref','sha256']
flags=['-mthumb','-mcpu=cortex-a9','-mfloat-abi=soft','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-fstack-usage']
frames=[];inputs=[]
for name in names:
 source=HERE/(name+'.c');obj=build/(name+'.o')
 subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),*flags,'-c',str(source),'-o',str(obj)],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
 inputs.append(dict(path=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
 for line in obj.with_suffix('.su').read_text().splitlines():
  location,size,kind=line.rsplit('\t',2)
  frames.append(dict(function=location.rsplit(':',1)[1],bytes=int(size),kind=kind,translation_unit=source.name))
probe=build/'sizes.c'
probe.write_text('#include "private_store.h"\n_Static_assert(sizeof(wdsv004_private_pool)==983636,"pool ARM layout");\n_Static_assert(sizeof(wdsv004_plan)==208,"plan ARM layout");\n_Static_assert(sizeof(wdsv004_snapshot)==44,"snapshot ARM layout");\n_Static_assert(sizeof(wdsv004_store)==16,"callback ARM layout");\n')
subprocess.run([str(sdk/'arm-vita-eabi-gcc.exe'),*flags,'-I',str(HERE),'-c',str(probe),'-o',str(build/'sizes.o')],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
small,large=163840+36,512000+36
policies=[]
for name,caps in [('existing',[small]*3),('hypothetical_ini_only',[large,small,small]),('hypothetical_all_large',[large]*3)]:
 pool=4+2*188+2*sum(caps);staging=sum(caps)
 policies.append(dict(policy=name,record_caps=caps,pool_bytes=pool,independent_replacement_bytes=staging,subtotal_bytes=pool+staging))
report=dict(scope='Own native code compiler frame metadata and fixed buffers; not client/Vita process memory or measured physical budget',compiler=subprocess.check_output([str(sdk/'arm-vita-eabi-gcc.exe'),'--version'],text=True).splitlines()[0],flags=flags,source_hashes=inputs,frames=frames,sum_reported_frames=sum(f['bytes'] for f in frames),policies=policies,limits=['Frame sizes are per function, not whole-program stack bounds; indirect callbacks, OS stack, libraries and interrupts excluded.','Replacement budget assumes all three payloads staged independently; game allocations and temporary serialization excluded.','No capacity changed; hypothetical policies do not establish compatibility or available Vita memory.'])
(HERE/'memory-budget-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(frames=frames,policies=policies)))