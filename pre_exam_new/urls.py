from django.urls import path,include

from .import exam_config_new
from.import exttchallocation
from.import extcordchairmanallocation
from.import extzonechairmanallocation
from.import extmarkview


urlpatterns = [

#--------------exam_configuration_start--------------------------------------------#
    path('api/v1/exam-add',exam_config_new.ExamConfiguration.as_view(),name='v1-exam-creation'),
    path('exam-add',exam_config_new.ExamConfiguration.as_view(),name='exam-creation'),
    path('api/v1/semester-wise-course-list',exam_config_new.SemesterwiseCourseList.as_view(),name = 'v1-semester-wise-course-list'),
    path('semester-wise-course-list',exam_config_new.SemesterwiseCourseList.as_view(),name = 'semester-wise-course-list'),
    path('api/v1/exam-list',exam_config_new.ExamList.as_view(),name='v1-exam-list-view'),
    path('exam-list',exam_config_new.ExamList.as_view(),name='exam-list-view'),
    path('api/v1/single/<pk>',exam_config_new.Examnotificationsingle.as_view(),name='single-view-notification'),
    path('api/v1/exam-add/<pk>',exam_config_new.ExamSingleGet.as_view(),name='exam-update-new'),
    path('api/v1/time-table-view/<pk>',exam_config_new.ExamWiseSchedule.as_view(),name='time-table-view-new'),
    path('api/v1/fee-table-view/<pk>',exam_config_new.PrgmSemWiseFeeList.as_view(),name='fee-table-view-new'),
    path('api/v1/exam-fetch/<pk>',exam_config_new.ExamSingleGet.as_view(),name='exam-fetch-new'),
    path('api/v1/exam-approve',exam_config_new.ExamApproval.as_view(),name='exam-approve-new'),
    path('api/v1/exam-delete',exam_config_new.ExamDelete.as_view(),name='exam-delete-new'),
    path('api/v1/exam-edit/<pk>',exam_config_new.ExamEditlist.as_view(),name='v1-examination-edit'),
    path('exam-edit/<pk>',exam_config_new.ExamEditlist.as_view(),name='examination-edit'),
    path('api/v1/exam-update',exam_config_new.Examedit.as_view(),name='v1-edit-examination'),
    path('api/v1/prg_group_list',exam_config_new.ProgrammeGroupList.as_view(),name='prg_group_list'),
    path('api/v1/prg_class_list',exam_config_new.ProgrammeClassList.as_view(),name='prg_class_list'),
    path('exam-update',exam_config_new.Examedit.as_view(),name='edit-examination'),
#-------------------------------------------------------------------------------------#

#------------exam_schedule_configuration_start--------------------------------------------
    path('api/v1/exam-schedule',exam_config_new.ExamSchedule.as_view(),name='v1-exam-schedule'),
    path('exam-schedule',exam_config_new.ExamSchedule.as_view(),name='exam-schedule'),
    path('exam-wise-prgm-sem',exam_config_new.ExamWisePrgmSem.as_view(),name='exam-wise-prgm-sem'),
    path('semester-wise-course-fetch',exam_config_new.SemesterwiseCourseFetch.as_view(),name='semester-wise-course-fetch'),
    path('api/v1/exam-schedule-list',exam_config_new.ExamScheduleListApi.as_view(),name='v1-exam-schedule-list'),
    path('exam-schedule-list',exam_config_new.ExamScheduleListApi.as_view(),name='exam-schedule-list'),



#-------------exam-time-table-view-----------------------------------------------------------
    path('exam-schedule-view/<pk>',exam_config_new.TimeTableViewApi.as_view(),name='exam-schedule-view'),
    path('exam-schedule-approval',exam_config_new.ExamScheduleApprovalApi.as_view(),name='exam-schedule-approval'),
    path('exam-schedule-delete',exam_config_new.ExamScheduleDeleteApi.as_view(),name='exam-schedule-delete'),
    path('api/v1/exam-schedule-edit/<pk>',exam_config_new.ExamScheduleEditApi.as_view(),name='v1-examination-schedule-edit'),
    path('exam-schedule-edit/<pk>',exam_config_new.ExamScheduleEditApi.as_view(),name='examination-schedule-edit'),
    path('exam-schedule-update',exam_config_new.ExamUpdateApi.as_view(),name='examination-schedule-update'),

    #--------------extend attendance & ca mark date -----------------------------------------------------------------
    path('extend-att-exam-date/<pk>',exam_config_new.ExtendExamDate.as_view(),name='extend-att-exam-date'),
    path('extend-date-attendance',exam_config_new.ExtendDateAttendance.as_view(),name='extend-date-attendance'),

    path('extend-ca-mark-date/<pk>',exam_config_new.ExtendCaMarkDate.as_view(),name='extend-ca-mark-date'),
    path('extend-ca-mark-last-date',exam_config_new.ExtendCaMarkLastDate.as_view(),name='extend-ca-mark-last-date'),

    path('add-admission-year/<pk>',exam_config_new.AddAdmissionYear.as_view(),name='add-admission-year'),
    path('update-admission-year',exam_config_new.UpdateAdmissionYear.as_view(),name='update-admission-year'),
    
    
    #---------------------Project rejection -------------------------------------------------------------------------------#
    path('reject-project-upload/<pk>',exam_config_new.RejectProjectUpload.as_view(),name='reject-project-upload'),
    path('extend-project-last-date',exam_config_new.ExtendProjectLastDate.as_view(),name='extend-project-last-date'),


    path('ext-dist', exttchallocation.ExtDistrictList.as_view(), name='ext-dist'),
    path('ext-prgm', exttchallocation.ExtProgrammeList.as_view(), name='ext-prgm'),
    path('ext-schm', exttchallocation.ExternalSchemes.as_view(), name='ext-schm'),

    path('ext-tchr', exttchallocation.TeacherFetch.as_view(), name='ext-tchr'),
    path('ext-cors', exttchallocation.ExtcoursesList.as_view(), name='ext-cors'),
    path('ext-allocation', exttchallocation.ExtProgramAllocation.as_view(), name='ext-allocation'),
    path('extcord-dist', extcordchairmanallocation.ExtcordDistrict.as_view(), name='extcord-dist'),
    path('extcord-fetch', extcordchairmanallocation.ExtcordFetch.as_view(), name='extcord-fetch'),
    path('extcord-collg', extcordchairmanallocation.ExtcordCollegesFetch.as_view(), name='extcord-collg'),
    path('extcordwise-collg', extcordchairmanallocation.ExtcordWiseCollegesFetch.as_view(), name='extcordwise-collg'),

    path('extcord-upload', extcordchairmanallocation.ExtcordUpload.as_view(), name='extcord-upload'),
    path('extcord-chairman', extzonechairmanallocation.Extcordchairman.as_view(), name='extcord-chairman'),
    path('extzone-collg', extzonechairmanallocation.ExtzoneCollegesFetch.as_view(), name='extzone-collg'),
    path('extzone-chairman', extzonechairmanallocation.ExtzoneFetch.as_view(), name='extzone-chairman'),
    path('extzone-upload', extzonechairmanallocation.ExtzoneUpload.as_view(), name='extzone-upload'),
    path('extcord-view', extmarkview.Extmarkchairmanview.as_view(), name='extcord-view'),
    path('extzone-view', extmarkview.ExtzoneviewFetch.as_view(), name='extzone-view'),
    path('exttch-view', extmarkview.ExttchviewFetch.as_view(), name='exttch-view'),
    path('exttch-edit', extmarkview.Exttchviewedit.as_view(), name='exttch-edit'),


]
